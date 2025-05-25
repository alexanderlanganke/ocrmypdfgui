#!/usr/bin/env python3
import threading
stop_event = threading.Event()
import ocrmypdf
import os
import sys
import warnings
import inspect
import gi
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

import pytesseract
import zipfile
import rarfile
import tempfile
import shutil


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
        if print_to_textview_func: # Check if a print function is provided
            GLib.idle_add(print_to_textview_func, error_message + "\n", "error")
        print(error_message) # Also print to console for non-GUI contexts if any
        return ""
    except Exception as e:
        error_message = f"Error OCRing image {image_path} with Tesseract: {e}"
        if print_to_textview_func:
            GLib.idle_add(print_to_textview_func, error_message + "\n", "error")
        print(error_message)
        return ""


def ocr_archive_file(archive_path, print_to_textview_func, progressbar_batch_func, ocrmypdfsettings, stop_event_ref, job_done_callback_ref):
    """
    Extracts images from a CBZ or CBR archive and prepares for PDF generation.
    """
    GLib.idle_add(print_to_textview_func, f"Starting processing for archive: {archive_path}\n", "default")
    GLib.idle_add(progressbar_batch_func, 0.0)
    temp_dir_path = None
    archive_opened_and_extracted = False
    image_files = []
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

    try:
        temp_dir_path = tempfile.mkdtemp()
        GLib.idle_add(print_to_textview_func, "Extracting images from archive...\n", "default")
        file_ext = os.path.splitext(archive_path)[1].lower()

        if file_ext == '.cbz':
            try:
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    try:
                        archive.extractall(temp_dir_path)
                        archive_opened_and_extracted = True
                    except Exception as e:
                        GLib.idle_add(print_to_textview_func, f"Error extracting CBZ archive {archive_path}: {e}\n", "error")
            except (zipfile.BadZipFile, FileNotFoundError) as e:
                GLib.idle_add(print_to_textview_func, f"Error opening CBZ archive {archive_path}: {e}\n", "error")
        elif file_ext == '.cbr':
            try:
                # rarfile.UNRAR_TOOL = "unrar" # Ensure unrar is in PATH or specify path
                with rarfile.RarFile(archive_path, 'r') as archive:
                    try:
                        archive.extractall(temp_dir_path)
                        archive_opened_and_extracted = True
                    except Exception as e: # Catches rarfile.ExtractionError, IOErrors etc.
                        GLib.idle_add(print_to_textview_func, f"Error extracting CBR archive {archive_path}: {e}\n", "error")
            except (rarfile.Error, FileNotFoundError) as e: # rarfile.Error is base for BadRarFile, NotRarFile etc.
                GLib.idle_add(print_to_textview_func, f"Error opening CBR archive {archive_path}: {e}\n", "error")
        else:
            GLib.idle_add(print_to_textview_func, f"Unsupported archive type: {archive_path}\n", "error")

        if stop_event_ref.is_set():
            GLib.idle_add(print_to_textview_func, "Job cancelled after archive extraction attempt.\n", "error")
            # Proceed to finally for cleanup

        elif archive_opened_and_extracted:
            GLib.idle_add(print_to_textview_func, "Image extraction complete. Collecting image files...\n", "default")
            for root, _, files in os.walk(temp_dir_path):
                if stop_event_ref.is_set(): break
                for f_name in files:
                    if stop_event_ref.is_set(): break
                    if os.path.splitext(f_name)[1].lower() in allowed_extensions:
                        image_files.append(os.path.join(root, f_name))
            
            if stop_event_ref.is_set():
                 GLib.idle_add(print_to_textview_func, "Job cancelled during image collection.\n", "error")
            else:
                image_files.sort()
                GLib.idle_add(print_to_textview_func, f"Found {len(image_files)} images.\n", "default")

                if not image_files:
                    GLib.idle_add(print_to_textview_func, f"No image files found in archive {archive_path}.\n", "skip")
                    return # Goes to finally

                # Conditional logic for output mode
                output_mode = ocrmypdfsettings.get("output_mode", "pdf") # Default to pdf if not set

                if output_mode == "sidecar_txt":
                    GLib.idle_add(print_to_textview_func, "Starting sidecar text file creation...\n", "default")
                    GLib.idle_add(progressbar_batch_func, 0.25) # Initial progress for sidecar mode
                    
                    aggregated_text = ""
                    total_images_for_ocr = len(image_files)
                    for i, img_path in enumerate(image_files):
                        if stop_event_ref.is_set():
                            GLib.idle_add(print_to_textview_func, "OCR job cancelled during text aggregation.\n", "error")
                            return # Goes to finally for cleanup
                        
                        # Update progress: 0.25 to 0.75 for text aggregation phase
                        current_progress = 0.25 + ( (i + 1) / total_images_for_ocr * 0.50 ) 
                        GLib.idle_add(progressbar_batch_func, current_progress)
                        GLib.idle_add(print_to_textview_func, f"OCR_ing image {i+1}/{total_images_for_ocr} for sidecar: {os.path.basename(img_path)}\n", "default")
                        
                        text = get_text_from_image(img_path, print_to_textview_func)
                        if text is None: # get_text_from_image might return None on error in some theoretical case
                            text = "" 
                        aggregated_text += f"--- Page {i+1}: {os.path.basename(img_path)} ---\n{text}\n\n"

                    if stop_event_ref.is_set(): # Re-check after loop
                        GLib.idle_add(print_to_textview_func, "OCR job cancelled after text aggregation.\n", "error")
                        return

                    temp_text_file_path = os.path.join(temp_dir_path, "ocr_text.txt")
                    try:
                        with open(temp_text_file_path, "w", encoding="utf-8") as tf:
                            tf.write(aggregated_text)
                    except IOError as e:
                        GLib.idle_add(print_to_textview_func, f"Error writing temporary text file: {e}\n", "error")
                        return # Goes to finally

                    original_archive_name_no_ext = os.path.splitext(os.path.basename(archive_path))[0]
                    original_archive_dir = os.path.dirname(archive_path)
                    is_original_cbr = archive_path.lower().endswith('.cbr')
                    
                    output_archive_name_base = original_archive_name_no_ext
                    # Determine if a new archive name is needed
                    if is_original_cbr or ocrmypdfsettings.get("new_archive_on_sidecar", True):
                        output_archive_name_base += "_ocr"
                    
                    output_archive_name = output_archive_name_base + ".cbz" # Output is always CBZ
                    output_archive_path = os.path.join(original_archive_dir, output_archive_name)

                    # If modifying in-place a CBZ (new_archive_on_sidecar is False and not a CBR)
                    # and output name is same as input, we still write to temp then move.
                    # This simplifies logic: always write to temp_output_cbz_path first.
                    if not ocrmypdfsettings.get("new_archive_on_sidecar", True) and not is_original_cbr:
                        # This means we intend to modify the original CBZ
                        output_archive_path = archive_path # Target the original path
                    
                    # Prevent accidental overwrite if new_archive_on_sidecar is True but names somehow clash (defensive)
                    if output_archive_path.lower() == archive_path.lower() and \
                       ocrmypdfsettings.get("new_archive_on_sidecar", True) and not is_original_cbr:
                        output_archive_path = os.path.join(original_archive_dir, original_archive_name_no_ext + "_ocr_new.cbz")

                    temp_output_cbz_path = os.path.join(temp_dir_path, "output_temp.cbz")

                    if stop_event_ref.is_set():
                        GLib.idle_add(print_to_textview_func, "Job cancelled before final archive creation.\n", "error")
                        return

                    try:
                        GLib.idle_add(print_to_textview_func, f"Creating/updating archive: {os.path.basename(output_archive_path)}\n", "default")
                        GLib.idle_add(progressbar_batch_func, 0.80) # Progress before zip creation

                        with zipfile.ZipFile(temp_output_cbz_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                            # Add extracted images (now relative to temp_dir_path)
                            for item_name in os.listdir(temp_dir_path):
                                item_full_path = os.path.join(temp_dir_path, item_name)
                                if os.path.isfile(item_full_path) and item_name != "ocr_text.txt" and item_name != "output_temp.cbz":
                                    # Add all original files from the temp extraction dir
                                    zf_out.write(item_full_path, arcname=item_name)
                            # Add OCR text file
                            zf_out.write(temp_text_file_path, arcname="ocr_text.txt")
                        
                        shutil.move(temp_output_cbz_path, output_archive_path)
                        GLib.idle_add(print_to_textview_func, f"Sidecar TXT archive operation complete: {output_archive_path}\n", "success")
                        GLib.idle_add(progressbar_batch_func, 0.9)

                    except Exception as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating sidecar archive: {e}\n", "error")
                        return

                elif output_mode == "pdf":
                    GLib.idle_add(print_to_textview_func, "Image collection and sorting complete. Starting PDF generation...\n", "default")
                    output_pdf_path = os.path.splitext(archive_path)[0] + "_ocr.pdf"
                    GLib.idle_add(print_to_textview_func, f"Creating searchable PDF: {output_pdf_path}\n", "default")
                    GLib.idle_add(progressbar_batch_func, 0.5) # Progress before OCR call

                    if stop_event_ref.is_set():
                        GLib.idle_add(print_to_textview_func, "Job cancelled before PDF generation.\n", "error")
                        return

                    try:
                        effective_settings = ocrmypdfsettings.copy()
                        if 'plugins' in effective_settings:
                            print("Note: 'plugins' key found in ocrmypdfsettings for archive processing. Removing for compatibility.")
                            del effective_settings['plugins']

                        ocrmypdf.ocr(
                            input_file=image_files,
                            output_file=output_pdf_path,
                            **effective_settings
                        )
                        GLib.idle_add(print_to_textview_func, f"Searchable PDF created successfully: {output_pdf_path}\n", "success")
                        GLib.idle_add(progressbar_batch_func, 0.9)
                    except ocrmypdf.exceptions.EncryptedPdfError as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating PDF: The operation resulted in an encrypted PDF, which is unexpected. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.PriorOcrFoundError as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating PDF: Prior OCR found, unexpected for image input. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.InputFileError as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating PDF: Invalid image file provided. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.MissingDependencyError as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating PDF: Missing system dependency. {e}\n", "error")
                        return
                    except ocrmypdf.exceptions.SubprocessOutputError as e:
                        GLib.idle_add(print_to_textview_func, f"Error creating PDF: A subprocess failed. {e}\n", "error")
                        return
                    except Exception as e:
                        GLib.idle_add(print_to_textview_func, f"An unexpected error occurred during PDF creation: {e}\n", "error")
                        return
                else: # Unknown mode
                    GLib.idle_add(print_to_textview_func, f"Unknown output mode: {output_mode}. Defaulting to PDF generation.\n", "error")
                    # Fallback to PDF generation (logic duplicated for clarity, could be refactored)
                    GLib.idle_add(print_to_textview_func, "Image collection and sorting complete. Starting PDF generation (fallback)...\n", "default")
                    output_pdf_path = os.path.splitext(archive_path)[0] + "_ocr.pdf"
                    GLib.idle_add(print_to_textview_func, f"Creating searchable PDF: {output_pdf_path}\n", "default")
                    GLib.idle_add(progressbar_batch_func, 0.5)

                    if stop_event_ref.is_set():
                        GLib.idle_add(print_to_textview_func, "Job cancelled before PDF generation (fallback).\n", "error")
                        return
                    try:
                        effective_settings = ocrmypdfsettings.copy()
                        if 'plugins' in effective_settings: del effective_settings['plugins']
                        ocrmypdf.ocr(input_file=image_files, output_file=output_pdf_path, **effective_settings)
                        GLib.idle_add(print_to_textview_func, f"Searchable PDF created successfully (fallback): {output_pdf_path}\n", "success")
                        GLib.idle_add(progressbar_batch_func, 0.9)
                    except Exception as e: # Simplified catch for fallback
                        GLib.idle_add(print_to_textview_func, f"An unexpected error occurred during PDF creation (fallback): {e}\n", "error")
                        return


    except tempfile.TemporaryFileError as e: # Specifically catch error during temp dir creation
        GLib.idle_add(print_to_textview_func, f"Error creating temporary directory: {e}\n", "error")
        # temp_dir_path would be None, so finally won't try to delete it.
    except Exception as e: # Catch-all for other unexpected errors, e.g., os.listdir if temp_dir_path is bad
        GLib.idle_add(print_to_textview_func, f"An unexpected error occurred processing archive {archive_path}: {e}\n", "error")
    finally:
        if temp_dir_path and os.path.exists(temp_dir_path):
            try:
                shutil.rmtree(temp_dir_path)
                GLib.idle_add(print_to_textview_func, "Temporary image directory cleaned up.\n", "default")
            except Exception as e:
                GLib.idle_add(print_to_textview_func, f"Error cleaning up temporary directory {temp_dir_path}: {e}\n", "error")
        GLib.idle_add(progressbar_batch_func, 1.0)
        GLib.idle_add(job_done_callback_ref)


def start_job(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback):
	stop_event.clear()
	t = threading.Thread(target=batch_ocr, args=(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback), daemon=True)
	t.start()
	return t


def ocr_run(file_path, ocrmypdfsettings, print_to_textview):
	print(ocrmypdfsettings)
	#runs ocrmypdf on given file
	try:
		print("Start OCR - " + file_path)
#		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["plugin_progressbar"])
		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["ocrmypdfgui.plugin_progressbar"])
		GLib.idle_add(print_to_textview, "OCR complete\n", "success")

		print("OCR complete.\n")
		return "OCR complete.\n"

	except ocrmypdf.exceptions.PriorOcrFoundError:
		GLib.idle_add(print_to_textview, "Prior OCR - Skipping\n", "skip")
		print("Prior OCR - Skipping\n")
		return "Prior OCR - Skipping\n"

	except ocrmypdf.exceptions.EncryptedPdfError:
		GLib.idle_add(print_to_textview, "PDF File is encrypted - Skipping.\n", "error")
		print("PDF File is encrypted. Skipping.\n")
		return "PDF File is encrypted. Skipping.\n"

	except ocrmypdf.exceptions.BadArgsError:
		GLib.idle_add(print_to_textview, "Bad arguments\n", "error")
		print("Bad arguments.\n")

	except:
		e = sys.exc_info()
		GLib.idle_add(print_to_textview, str(e))
		GLib.idle_add(print_to_textview, "\n")
		#time.sleep(0.2)
		print(e)
		return "Error.\n"

def batch_ocr(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings, job_done_callback):
	# walks through given path and uses OCR Function on every pdf in path
	try:
		GLib.idle_add(progressbar_batch, 0.0) #resets progressbar_batch
		progress_precision = 0.0
		percent_step = 0.0
		if(os.path.isfile(dir_path)==True):
			#Run OCR on single file
			if stop_event.is_set():
				print("OCR job cancelled.")
				GLib.idle_add(print_to_textview, "OCR job cancelled.\n", "error")
				GLib.idle_add(job_done_callback) # Ensure callback is called
				return

			file_ext = os.path.splitext(dir_path)[1].lower() # Ensure lowercase for comparison
			if file_ext == '.cbz' or file_ext == '.cbr':
				# Call ocr_archive_file and then return as it handles its own completion.
				ocr_archive_file(dir_path, print_to_textview, progressbar_batch, ocrmypdfsettings, stop_event, job_done_callback)
				return 
			elif file_ext == '.pdf':
				print("Path:" + dir_path + "\n")
				GLib.idle_add(print_to_textview, "File: " + dir_path + " - ", "default")
				result = ocr_run(dir_path, ocrmypdfsettings, print_to_textview)
				# GLib.idle_add(progressbar_batch, 1.0) # Handled by plugin for PDF, or ocr_job_finished_or_stopped
				# For single PDF, job_done_callback is called in the finally block
			# else: # Handle unsupported single file types
				# GLib.idle_add(print_to_textview, f"Unsupported file type: {file_ext}\n", "error")
				# No specific result, job_done_callback will be called in finally
		elif(os.path.isdir(dir_path)==True):
			number_of_files = 0
			# First pass: count PDF files for progress calculation (existing logic)
			# TODO: Consider if CBZ/CBR in directory mode should be counted or handled.
			# For now, directory mode only processes PDFs as per original logic.
			for dir_name, subdirs, file_list in os.walk(dir_path):
				if stop_event.is_set():
					print("OCR job cancelled.")
					GLib.idle_add(print_to_textview, "OCR job cancelled.\n", "error")
					break 
				for filename in file_list:
					if stop_event.is_set():
						print("OCR job cancelled.")
						GLib.idle_add(print_to_textview, "OCR job cancelled.\n", "error")
						break
					file_ext = os.path.splitext(filename)[1]
					if file_ext == '.pdf':
						number_of_files=number_of_files+1

				if number_of_files >0:
					percent_step = 1/number_of_files	#1 = 100%
					print("percent_step: " + str(percent_step) + " - " + "number_of_files: " + str(number_of_files))
			for dir_name, subdirs, file_list in os.walk(dir_path):
				if stop_event.is_set():
					print("OCR job cancelled.")
					GLib.idle_add(print_to_textview, "OCR job cancelled.\n", "error")
					break
				print(file_list)

				for filename in file_list:
					if stop_event.is_set():
						print("OCR job cancelled.")
						GLib.idle_add(print_to_textview, "OCR job cancelled.\n", "error")
						break
					file_ext = os.path.splitext(filename)[1]
					if file_ext == '.pdf':
						full_path = dir_name + '/' + filename

						print("Path:" + full_path + "\n")
						GLib.idle_add(print_to_textview, "File: " + full_path + " - ", "default")
						result = ocr_run(full_path, ocrmypdfsettings, print_to_textview)
						progress_precision = progress_precision + percent_step #necessary to hit 100 by incrementing
						print(progress_precision)
						GLib.idle_add(progressbar_batch, progress_precision) #sets progressbar_batch to current progress
			# If no PDFs found in directory walk, ensure progress is set to 100%
			if number_of_files == 0 and not stop_event.is_set():
				GLib.idle_add(progressbar_batch, 1.0)


		else: # Not a file, not a directory (should not happen with FileChooserDialog)
			print(f"Error: Path is not a file or directory: {dir_path}")
			GLib.idle_add(print_to_textview, f"Error: Path is not a file or directory: {dir_path}\n", "error")
			# job_done_callback will be called in finally
	finally:
		# This finally block will execute for single PDF, directory processing, or if it's not a file/dir.
		# For archives (.cbz/.cbr), ocr_archive_file handles its own job_done_callback.
		# We only call job_done_callback here if it's not an archive that was processed.
		file_ext_final = os.path.splitext(dir_path)[1].lower() if os.path.isfile(dir_path) else ""
		if not (os.path.isfile(dir_path) and (file_ext_final == '.cbz' or file_ext_final == '.cbr')):
			GLib.idle_add(print_to_textview, "OCR process ended.\n", "default")
			GLib.idle_add(job_done_callback)


def get_api_options():
	sig = inspect.signature(ocrmypdf.ocr)
	#print (str(sig))
	dict = {}
	for param in sig.parameters.values():
		if (param.kind == param.KEYWORD_ONLY):
			#print(param.name)
			#print(param.annotation)
			if str(param.annotation)[8:-2] == "bool" or str(param.annotation)[8:-2] == "int" or str(param.annotation)[8:-2] == "float" or str(param.annotation)[8:-2] == "str" or str(param.annotation) == "typing.Iterable[str]":
				if(str(param.annotation) == "typing.Iterable[str]"):
					dict[param.name] = str(param.annotation)
				else:
					dict[param.name] = str(param.annotation)[8:-2]

	return dict
