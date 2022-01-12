import googlemaps
gmaps = googlemaps.Client(key='AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk')
import boto
import boto3
from collections import defaultdict

# Google Maps API for pulling place details and photos
def getPlace_details(address, identifier, text):

    # Declare a dictionary
    image_dict = defaultdict(list)

    global c
    c=0

    try:

        # API Call
        result = gmaps.find_place(address, input_type = text, language="en")

        plc_id = result['candidates'][0]['place_id']

        plc_details = gmaps.place(plc_id, fields=["formatted_address", "geometry", "photo"])

        result = plc_details['result']

        for el in result['photos']:

            ph_refs = [el['photo_reference'] for x in el]

            for ph in list(set(ph_refs)):

                c = c + 1

                # Download / open photo
                img_obj = gmaps.places_photo(ph, max_width = 500, max_height = 400)

                print(img_obj)

                s3 = boto3.client('s3')

                with open('photos/{}_image_{}.png'.format(identifier, c), 'wb') as data:
                    for chunk in img_obj:
                        data.write(chunk)

                s3.upload_file('photos/{}_image_{}.png'.format(identifier, c), 'gmaps-images', 'prop-images/{}_image_{}.png'.format(identifier, c))

                # Create a list of dictionary of images for carousel
                url = 's3://gmaps-images/prop-images/{}_image_{}.png'.format(identifier, c)

                image_dict[identifier].append(url)

        return image_dict

    except Exception as e:
        print(e)
        pass
