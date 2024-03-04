from __future__ import print_function

import os
import tba
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging, coloredlogs, verboselogs


# If modifying these scopes, delete the file token.json.
SCOPES = [
	"https://www.googleapis.com/auth/spreadsheets.readonly",
	"https://www.googleapis.com/auth/presentations",
	"https://www.googleapis.com/auth/drive"
]


def init(logger):
	"""Shows basic usage of the Slides API.
	Prints the number of slides and elements in a sample presentation.
	"""
	logging.info("Initializing Google Drive API")
	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.json'):
		creds = Credentials.from_authorized_user_file('token.json', SCOPES)
	# If there are no (valid) credentials available, let the user log in.
	try:
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'creds.json', SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			logger.success("Google Drive API Token received")
			logger.info("Caching Google Drive API Token in system")
			with open('token.json', 'w') as token:
				token.write(creds.to_json())
			logger.success("Google Drive API Token cached")

	except Exception as e:
		print(e)
		logger.error("Credentials require refresh, deleting expired token")
		if os.path.exists('token.json'):
			os.remove('token.json')
		init(logger)


def get_sheet_data(logger):
	sheet_id = tba.access_storage("sheet_id", logger)
	logger.info("Gathering Scouting Data from Google Sheet")
	try:
		token_path = 'token.json'
		creds = Credentials.from_authorized_user_file(token_path)
		service = build('sheets', 'v4', credentials=creds)
		data = service.spreadsheets().values().get(range="Form Responses 1",
		spreadsheetId=sheet_id).execute().get('values')
		return data

	except HttpError as error:
		print(f"An error occurred: {error}")
		print("Sheet not found")

def sheets_lookup(team, data, l):
	for row in data:
		if (row[1] == team):
			return row

def replace_text_with_images(presentation_id, placeholders_to_images, logger):
	# Authenticate and create the service object
	token_path = 'token.json'

	creds = Credentials.from_authorized_user_file(token_path)
	service = build('slides', 'v1', credentials=creds)

	# Retrieve the presentation
	presentation = service.presentations().get(presentationId=presentation_id).execute()
	slides = presentation.get('slides', [])

	requests = []  # Holds all our requests

	# Iterate over all slides and placeholders
	for slide_id, slide in enumerate(slides):
		for element in slide['pageElements']:
			if 'shape' in element and 'text' in element['shape']:
				text_elements = element['shape']['text']['textElements']
				for text_element in text_elements:
					if 'textRun' in text_element and 'content' in text_element['textRun']:
						text_content = text_element['textRun']['content']
						if text_content.strip() in placeholders_to_images:
							# Calculate image size and position
							image_url = placeholders_to_images[text_content.strip()]
							size = element['size']
							transform = element['transform']

							# For some reason I have no clue about, the scale and translate factor is off
							# These lines fix it
							transform['translateX'] = transform['translateX'] - 500000
							transform['scaleX'] = transform['scaleY']



							# Create requests to replace text with image
							requests.append({
								'createImage': {
									'url': "https://drive.google.com/uc?id="+image_url.split("=")[1],
									'elementProperties': {
										'pageObjectId': slide['objectId'],
										'size': size,
										'transform': transform
									}
								}
							})
							# Create request to delete the placeholder text box
							requests.append({'deleteObject': {'objectId': element['objectId']}})
	

	# Execute the batch update
	try:
		if requests:
			body = {
				'requests': requests
			}
			response = service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
			print(f"Updated presentation with ID: {presentation_id}")
			return response

	except:
		return None


def create_presentation(title, logger):
	"""
		Creates the Presentation the user has access to.
		Load pre-authorized user credentials from the environment.
		TODO(developer) - See https://developers.google.com/identity
		for guides on implementing OAuth2 for the application.
		"""
	# creds, _ = google.auth.default()
	# pylint: disable=maybe-no-member

	token_path = 'token.json'
	creds = Credentials.from_authorized_user_file(token_path)

	try:
		service = build('slides', 'v1', credentials=creds)
		body = {
			'title': title
		}
		presentation = service.presentations().create(body=body).execute()
		print(f"Created presentation with ID: {(presentation.get('presentationId'))}")
		return presentation

	except HttpError as error:
		logger.error(f"An error occurred: {error}")
		logger.critical("Presentation not created")
		return error

def copy_presentation(presentation_id, copy_title, logger):
	"""
		   Creates the copy Presentation the user has access to.
		   Load pre-authorized user credentials from the environment.
		   TODO(developer) - See https://developers.google.com/identity
		   for guides on implementing OAuth2 for the application.
		   """

	token_path = 'token.json'
	creds = Credentials.from_authorized_user_file(token_path)
	# pylint: disable=maybe-no-member
	try:
		drive_service = build('drive', 'v3', credentials=creds)
		body = {
			'name': copy_title
		}
		drive_response = drive_service.files().copy(fileId=presentation_id, body=body).execute()
		presentation_copy_id = drive_response.get("id")

	except HttpError as error:
		print(f"An error occurred: {error}")
		print("Presentations not copied")
		return error

	return presentation_copy_id


def replace_all_text_in_slides(presentation_id, replacements_dict, logger):
	token_path = 'token.json'
	creds = Credentials.from_authorized_user_file(token_path)

	try:
		service = build('slides', 'v1', credentials=creds)
		requests = []  # Hold all requests to modify the slides

		# Go through each replacement pair in the dictionary
		for search_text, replace_text in replacements_dict.items():
			# Add a replace all text request for the presentation
			requests.append(
			{
				"replaceAllText": {
					"replaceText": replace_text,
					"containsText": 
					{
						"text": search_text,
						"matchCase": True
					}
				}
			})

		# Only make a batchUpdate call if there are requests to process
		if requests:
			body = {'requests': requests}
			response = service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
			return response

		return "No text replacements specified."

	except HttpError as error:
		print(f"An error occurred: {error}")
		return error


from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

def update_textbox_backgrounds(presentation_id, substrings_colors_dict, logger):
	token_path = 'token.json'
	creds = None
	# The following line should be replaced with your method of creating Google credentials
	creds = Credentials.from_authorized_user_file(token_path)

	if not creds or not creds.valid:
		print("Invalid or non-existent credentials.")
		return

	try:
		service = build('slides', 'v1', credentials=creds)
		# Retrieve the presentation slides
		presentation = service.presentations().get(presentationId=presentation_id).execute()
		slides = presentation.get('slides', [])

		requests = []

		for slide in slides:
			page_elements = slide.get('pageElements', [])
			for element in page_elements:
				if 'shape' in element and 'text' in element['shape']:
					text_elements = element['shape']['text']['textElements']
					for text_element in text_elements:
						if 'textRun' in text_element and 'content' in text_element['textRun']:
							text_content = text_element['textRun']['content']
							for substring, hex_color in substrings_colors_dict.items():
								if substring in text_content:
									# Convert hex color to RGB
									if hex_color.startswith('#'):
										hex_color = hex_color[1:]
									rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

									# Create request to update the background color
									requests.append({
										'updateShapeProperties': {
											'objectId': element['objectId'],
											'fields': 'shapeBackgroundFill.solidFill.color',
											'shapeProperties': {
												'shapeBackgroundFill': {
													'solidFill': {
														'color': {
															'rgbColor': {
																'red': rgb_color[0] / 255.0,
																'green': rgb_color[1] / 255.0,
																'blue': rgb_color[2] / 255.0
															}
														}
													}
												}
											}
										}
									})

		# Execute the batch update request
		if requests:
			body = {'requests': requests}
			response = service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
			return response
		else:
			return "No text box with the specified substrings found."

	except GoogleAuthError as auth_error:
		print(f"An authentication error occurred: {auth_error}")
		return None
	except HttpError as http_error:
		print(f"An HTTP error occurred: {http_error}")
		return None



