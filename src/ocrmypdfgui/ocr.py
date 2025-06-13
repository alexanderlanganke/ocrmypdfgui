#!/usr/bin/env python3
import threading
stop_event = threading.Event()
import ocrmypdf
import os
import sys
import warnings
import inspect
import time
import logging

from PIL import Image

warnings.simplefilter('ignore', Image.DecompressionBombWarning)

import pytesseract
import zipfile
import rarfile
import tempfile
import shutil

logger = logging.getLogger(__name__)


def get_text_from_image(image_path, print_to_textview_func):
    """
    Extracts text from a single image using pytesseract.

    Args:
        image_path (str): The path to the image file.
        print_to_textview_func (callable): Function to print messages to the GUI.

    Returns:
        str: The extracted text, or an empty string if OCR fails.
    """
    try:
        text = pytesseract.image_to_string(image_path)
        return text
    except pytesseract.TesseractNotFoundError:
        error_message = "Error: Tesseract is not installed or not in your PATH."
        if print_to_textview_func:
            print_to_textview_func(error_message + "\n", "error")
        print(error_message)
        return ""
    except Exception as e:
        error_message = f"Error OCRing image {image_path} with Tesseract: {e}"
        if print_to_textview_func:
            print_to_textview_func(error_message + "\n", "error")
        print(error_message)
        return ""


def ocr_archive_file(archive_path, print_to_textview_func, progressbar_batch_func, ocrmypdfsettings, stop_event_ref, job_done_callback_ref):
    """
    Extracts images from a CBZ or CBR archive and prepares for PDF generation.
    """
    print_to_textview_func(f"Starting processing for archive: {archive_path}\n", "default")
    progressbar_batch_func(0.0)
    temp_dir_path = None
    archive_opened_and_extracted = False
    image_files = []
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

    try:
        temp_dir_path = tempfile.mkdtemp()
        print_to_textview_func(f"Extracting images from archive...\n", "default")
        file_ext = os.path.splitext(archive_path)[1].lower()

        # Check for sidecar txt before extraction
        if file_ext in ['.cbz', '.cbr']:
            with zipfile.ZipFile(archive_path, 'r') as archive:
                if 'ocr_text.txt' in archive.namelist():
                    print_to_textview_func(f"Archive {os.path.basename(archive_path)} already contains a sidecar TXT file. Skipping.\n", "skip")
                    return
        if file_ext == '.cbz':
            try:
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    try:
                        archive.extractall(temp_dir_path)
                        archive_opened_and_extracted = True
                    except Exception as e:
                        print_to_textview_func(f"Error extracting CBZ archive {archive_path}: {e}\n", "error")
            except (zipfile.BadZipFile, FileNotFoundError) as e:
                print_to_textview_func(f"Error opening CBZ archive {archive_path}: {e}\n", "error")
        elif file_ext == '.cbr':
            try:
                with rarfile.RarFile(archive_path, 'r') as archive:
                    try:
                        archive.extractall(temp_dir_path)
                        archive_opened_and_extracted = True
                    except Exception as e:
                        print_to_textview_func(f"Error extracting CBR archive {archive_path}: {e}\n", "error")
            except (rarfile.Error, FileNotFoundError) as e:
                print_to_textview_func(f"Error opening CBR archive {archive_path}: {e}\n", "error")
        else:
            print_to_textview_func(f"Unsupported archive type: {archive_path}\n", "error")

        if stop_event_ref.is_set():
            print_to_textview_func("Job cancelled after archive extraction attempt.\n", "error")
        elif archive_opened_and_extracted:
            print_to_textview_func("Image extraction complete. Collecting image files...\n", "default")
            for root, _, files in os.walk(temp_dir_path):
                if stop_event_ref.is_set(): break
                for f_name in files:
                    if stop_event_ref.is_set(): break
                    if os.path.splitext(f_name)[1].lower() in allowed_extensions:
                        image_files.append(os.path.join(root, f_name))
            if stop_event_ref.is_set():
                print_to_textview_func("Job cancelled during image collection.\n", "error")
            else:
                image_files.sort()
                print_to_textview_func(f"Found {len(image_files)} images.\n", "default")
                if not image_files:
                    print_to_textview_func(f"No image files found in archive {archive_path}.\n", "skip")
                    return
                output_mode = ocrmypdfsettings.get("output_mode", "pdf")
                if output_mode == "sidecar_txt":
                    print_to_textview_func("Starting sidecar text file creation...\n", "default")
                    progressbar_batch_func(0.25)
                    aggregated_text = ""
                    total_images_for_ocr = len(image_files)
                    for i, img_path in enumerate(image_files):
                        if stop_event_ref.is_set():
                            print_to_textview_func("OCR job cancelled during text aggregation.\n", "error")
                            return
                        current_progress = 0.25 + ( (i + 1) / total_images_for_ocr * 0.50 )
                        progressbar_batch_func(current_progress)
                        print_to_textview_func(f"OCR_ing image {i+1}/{total_images_for_ocr} for sidecar: {os.path.basename(img_path)}\n", "default")
                        text = get_text_from_image(img_path, print_to_textview_func)
                        if text is None:
                            text = ""
                        aggregated_text += f"--- Page {i+1}: {os.path.basename(img_path)} ---\n{text}\n\n"
                    if stop_event_ref.is_set():
                        print_to_textview_func("OCR job cancelled after text aggregation.\n", "error")
                        return
                    temp_text_file_path = os.path.join(temp_dir_path, "ocr_text.txt")
                    try:
                        with open(temp_text_file_path, "w", encoding="utf-8") as tf:
                            tf.write(aggregated_text)
                    except IOError as e:
                        print_to_textview_func(f"Error writing temporary text file: {e}\n", "error")
                        return
                    original_archive_name_no_ext = os.path.splitext(os.path.basename(archive_path))[0]
                    original_archive_dir = os.path.dirname(archive_path)
                    is_original_cbr = archive_path.lower().endswith('.cbr')
                    output_archive_name_base = original_archive_name_no_ext
                    if is_original_cbr or ocrmypdfsettings.get("new_archive_on_sidecar", True):
                        output_archive_name_base += "_ocr"
                    output_archive_name = output_archive_name_base + ".cbz"
                    output_archive_path = os.path.join(original_archive_dir, output_archive_name)
                    if not ocrmypdfsettings.get("new_archive_on_sidecar", True) and not is_original_cbr:
                        output_archive_path = archive_path
                    if output_archive_path.lower() == archive_path.lower() and \
                       ocrmypdfsettings.get("new_archive_on_sidecar", True) and not is_original_cbr:
                        output_archive_path = os.path.join(original_archive_dir, original_archive_name_no_ext + "_ocr_new.cbz")
                    temp_output_cbz_path = os.path.join(temp_dir_path, "output_temp.cbz")
                    if stop_event_ref.is_set():
                        print_to_textview_func("Job cancelled before final archive creation.\n", "error")
                        return
                    try:
                        print_to_textview_func(f"Creating/updating archive: {os.path.basename(output_archive_path)}\n", "default")
                        progressbar_batch_func(0.80)
                        with zipfile.ZipFile(temp_output_cbz_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                            for root_dir, dirs, files in os.walk(temp_dir_path):
                                for file in files:
                                    abs_file_path = os.path.join(root_dir, file)
                                    rel_path = os.path.relpath(abs_file_path, temp_dir_path)
                                    if file == "output_temp.cbz":
                                        continue
                                    if rel_path == "ocr_text.txt":
                                        continue
                                    zf_out.write(abs_file_path, arcname=rel_path)
                            zf_out.write(temp_text_file_path, arcname="ocr_text.txt")
                        shutil.move(temp_output_cbz_path, output_archive_path)
                        print_to_textview_func(f"Sidecar TXT archive operation complete: {output_archive_path}\n", "success")
                        progressbar_batch_func(0.9)
                    except Exception as e:
                        print_to_textview_func(f"Error creating sidecar archive: {e}\n", "error")
                        return
                elif output_mode == "pdf":
                    print_to_textview_func("Image collection and sorting complete. Starting PDF generation...\n", "default")
                    temp_images_pdf = os.path.join(temp_dir_path, "images_combined.pdf")
                    images_to_pdf(image_files, temp_images_pdf)
                    output_pdf_path = os.path.splitext(archive_path)[0] + "_ocr.pdf"
                    print_to_textview_func(f"Creating searchable PDF: {output_pdf_path}\n", "default")
                    progressbar_batch_func(0.5)
                    if stop_event_ref.is_set():
                        print_to_textview_func("Job cancelled before PDF generation.\n", "error")
                        return
                    try:
                        effective_settings = ocrmypdfsettings.copy()
                        if 'plugins' in effective_settings:
                            del effective_settings['plugins']
                        filtered_settings = filter_ocrmypdf_args(effective_settings)
                        ocrmypdf.ocr(
                            input_file=temp_images_pdf,
                            output_file=output_pdf_path,
                            **filtered_settings
                        )
                        print_to_textview_func(f"Searchable PDF created successfully: {output_pdf_path}\n", "success")
                        progressbar_batch_func(0.9)
                    except ocrmypdf.exceptions.EncryptedPdfError as e:
                        print_to_textview_func(f"Error creating PDF: The operation resulted in an encrypted PDF, which is unexpected. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.PriorOcrFoundError as e:
                        print_to_textview_func(f"Error creating PDF: Prior OCR found, unexpected for image input. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.InputFileError as e:
                        print_to_textview_func(f"Error creating PDF: Invalid image file provided. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.MissingDependencyError as e:
                        print_to_textview_func(f"Error creating PDF: Missing system dependency. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.SubprocessOutputError as e:
                        print_to_textview_func(f"Error creating PDF: A subprocess failed. {e}\n", "error")
                        return
                    except Exception as e:
                        print_to_textview_func(f"An unexpected error occurred during PDF creation: {e}\n", "error")
                        return
                else:
                    print_to_textview_func(f"Unknown output mode: {output_mode}. Defaulting to PDF generation.\n", "error")
                    print_to_textview_func("Image collection and sorting complete. Starting PDF generation (fallback)...\n", "default")
                    output_pdf_path = os.path.splitext(archive_path)[0] + "_ocr.pdf"
                    print_to_textview_func(f"Creating searchable PDF: {output_pdf_path}\n", "default")
                    progressbar_batch_func(0.5)
                    if stop_event_ref.is_set():
                        print_to_textview_func("Job cancelled before PDF generation (fallback).\n", "error")
                        return
                    try:
                        effective_settings = ocrmypdfsettings.copy()
                        if 'plugins' in effective_settings: del effective_settings['plugins']
                        filtered_settings = filter_ocrmypdf_args(effective_settings)
                        ocrmypdf.ocr(input_file=image_files, output_file=output_pdf_path, **filtered_settings)
                        print_to_textview_func(f"Searchable PDF created successfully (fallback): {output_pdf_path}\n", "success")
                        progressbar_batch_func(0.9)
                    except Exception as e:
                        print_to_textview_func(f"An unexpected error occurred during PDF creation (fallback): {e}\n", "error")
                        return
    except tempfile.TemporaryFileError as e:
        print_to_textview_func(f"Error creating temporary directory: {e}\n", "error")
    except Exception as e:
        print_to_textview_func(f"An unexpected error occurred processing archive {archive_path}: {e}\n", "error")
    finally:
        if temp_dir_path and os.path.exists(temp_dir_path):
            try:
                shutil.rmtree(temp_dir_path)
                print_to_textview_func("Temporary image directory cleaned up.\n", "default")
            except Exception as e:
                print_to_textview_func(f"Error cleaning up temporary directory {temp_dir_path}: {e}\n", "error")
        progressbar_batch_func(1.0)
        job_done_callback_ref()


def start_job(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback):
	stop_event.clear()
	t = threading.Thread(target=batch_ocr, args=(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback), daemon=True)
	t.start()
	return t


def ocr_run(file_path, ocrmypdfsettings, print_to_textview):
    print(ocrmypdfsettings)
    # Only pass valid arguments to ocrmypdf.ocr
    valid_args = get_api_options().keys()
    filtered_settings = {k: v for k, v in ocrmypdfsettings.items() if k in valid_args}
    try:
        print("Start OCR - " + file_path)
        filtered_settings = filter_ocrmypdf_args(ocrmypdfsettings)
        ocr = ocrmypdf.ocr(file_path, file_path, **filtered_settings)  # Removed plugins argument
        print_to_textview("OCR complete\n", "success")
        print("OCR complete.\n")
        return "OCR complete.\n"
    except ocrmypdf.exceptions.PriorOcrFoundError:
        print_to_textview("Prior OCR - Skipping\n", "skip")
        print("Prior OCR - Skipping\n")
        return "Prior OCR - Skipping\n"
    except ocrmypdf.exceptions.EncryptedPdfError:
        print_to_textview("PDF File is encrypted - Skipping.\n", "error")
        print("PDF File is encrypted. Skipping.\n")
        return "PDF File is encrypted. Skipping.\n"
    except ocrmypdf.exceptions.BadArgsError:
        print_to_textview("Bad arguments\n", "error")
        print("Bad arguments.\n")
    except:
        e = sys.exc_info()
        print_to_textview(str(e), "error")
        print_to_textview("\n", "error")
        print(e)
        return "Error.\n"

def batch_ocr(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback):
	# walks through given path and uses OCR Function on every pdf in path
	try:
		progressbar_batch(0.0) #resets progressbar_batch
		progress_precision = 0.0
		percent_step = 0.0
		if(os.path.isfile(dir_path)==True):
			#Run OCR on single file
			if stop_event.is_set():
				print("OCR job cancelled.")
				print_to_textview("OCR job cancelled.\n", "error")
				job_done_callback() # Ensure callback is called
				return

			file_ext = os.path.splitext(dir_path)[1].lower() # Ensure lowercase for comparison
			if file_ext == '.cbz' or file_ext == '.cbr':
				# Call ocr_archive_file and then return as it handles its own completion.
				ocr_archive_file(dir_path, print_to_textview, progressbar_batch, ocrmypdfsettings, stop_event, job_done_callback)
				return 
			elif file_ext == '.pdf':
				print("Path:" + dir_path + "\n")
				print_to_textview("File: " + dir_path + " - ", "default")
				result = ocr_run(dir_path, ocrmypdfsettings, print_to_textview)
				# GLib.idle_add(progressbar_batch, 1.0) # Handled by plugin for PDF, or ocr_job_finished_or_stopped
				# For single PDF, job_done_callback is called in the finally block
			# else: # Handle unsupported single file types
				# GLib.idle_add(print_to_textview, f"Unsupported file type: {file_ext}\n", "error")
				# No specific result, job_done_callback will be called in finally
		elif(os.path.isdir(dir_path)==True):
			number_of_files = 0
			# First pass: count PDF, CBZ, and CBR files for progress calculation
			for dir_name, subdirs, file_list in os.walk(dir_path):
				if stop_event.is_set():
					print("OCR job cancelled.")
					print_to_textview("OCR job cancelled.\n", "error")
					break
				for filename in file_list:
					if stop_event.is_set():
						print("OCR job cancelled.")
						print_to_textview("OCR job cancelled.\n", "error")
						break
					file_ext = os.path.splitext(filename)[1].lower()
					if file_ext in ['.pdf', '.cbz', '.cbr']:
						number_of_files += 1

			if number_of_files > 0:
				percent_step = 1 / number_of_files  # 1 = 100%
				print("percent_step: " + str(percent_step) + " - " + "number_of_files: " + str(number_of_files))

			progress_precision = 0.0
			for dir_name, subdirs, file_list in os.walk(dir_path):
				if stop_event.is_set():
					print("OCR job cancelled.")
					print_to_textview("OCR job cancelled.\n", "error")
					break
				print(file_list)

				for filename in file_list:
					if stop_event.is_set():
						print("OCR job cancelled.")
						print_to_textview("OCR job cancelled.\n", "error")
						break
					file_ext = os.path.splitext(filename)[1].lower()
					full_path = os.path.join(dir_name, filename)
					if file_ext == '.pdf':
						print("Path:" + full_path + "\n")
						print_to_textview("File: " + full_path + " - ", "default")
						result = ocr_run(full_path, ocrmypdfsettings, print_to_textview)
					elif file_ext in ['.cbz', '.cbr']:
						print("Archive:" + full_path + "\n")
						print_to_textview("Archive: " + full_path + " - ", "default")
						ocr_archive_file(full_path, print_to_textview, progressbar_batch, ocrmypdfsettings, stop_event, job_done_callback)
					else:
						continue  # skip unsupported files

					progress_precision += percent_step
					print(progress_precision)
					progressbar_batch(progress_precision)  # sets progressbar_batch to current progress

			# If no supported files found in directory walk, ensure progress is set to 100%
			if number_of_files == 0 and not stop_event.is_set():
				progressbar_batch(1.0)


		else: # Not a file, not a directory (should not happen with FileChooserDialog)
			print(f"Error: Path is not a file or directory: {dir_path}")
			print_to_textview(f"Error: Path is not a file or directory: {dir_path}\n", "error")
			# job_done_callback will be called in finally
	finally:
		# This finally block will execute for single PDF, directory processing, or if it's not a file/dir.
		# For archives (.cbz/.cbr), ocr_archive_file handles its own job_done_callback.
		# We only call job_done_callback here if it's not an archive that was processed.
		file_ext_final = os.path.splitext(dir_path)[1].lower() if os.path.isfile(dir_path) else ""
		if not (os.path.isfile(dir_path) and (file_ext_final == '.cbz' or file_ext_final == '.cbr')):
			print_to_textview("OCR process ended.\n", "default")
			job_done_callback()


def get_api_options():
	sig = inspect.signature(ocrmypdf.ocr)
	#print (str(sig))
	dict = {}
	for param in sig.parameters.values():
		if (param.kind == param.KEYWORD_ONLY):
			#print(param.name)
			#print(param.annotation)
			if str(param.annotation)[8:-2] == "bool" or str(param.annotation)[8:-2] == "int" or str(param.annotation)[8:-2] == "float" or str(param.annotation)[8:-2] == "str" or str(param.annotation) == "typing.Iterable[str]":
				if str(param.annotation) == "typing.Iterable[str]":
					dict[param.name] = str(param.annotation)
				else:
					dict[param.name] = str(param.annotation)[8:-2]

	return dict

def images_to_pdf(image_files, output_pdf_path):
    """Convert a list of image files to a single PDF."""
    images = []
    for img_path in image_files:
        img = Image.open(img_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)
    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
    return output_pdf_path

def filter_ocrmypdf_args(settings):
    """Return a dict with only valid ocrmypdf.ocr() keyword arguments."""
    valid_args = get_api_options().keys()
    return {k: v for k, v in settings.items() if k in valid_args}
