import csv
import os

from .selenium import MapsSelenium
from .service import MapService


def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles


def run(*args, **kwargs):
    folder = os.getcwd()
    for file_name in getListOfFiles(folder):
        if not os.path.isfile(file_name) or not file_name.endswith('.csv'):
            continue

        print('Working with', file_name)
        maps_service = MapService()
        try:
            object_list = maps_service.get_list(file=file_name)
        except UnicodeDecodeError:
            print('Unable to work with', file_name)
            continue

        if not object_list:
            continue

        for obj in object_list:
            MapsSelenium(entity=obj)

        with open(file_name, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'location',
                'name',
                'business',
                'description',
                'directions',
                'related_searches'
            ])
            writer.writeheader()

            for obj in object_list:
                data = dict(
                    location=obj.location,
                    name='{main_keyword} {city} - {name}'.format(
                        main_keyword=obj.main_keyword,
                        city=obj.location_city,
                        name=obj.name
                    ),
                    business=(
                        '{name}\n{address}\n{phone}\n{url}\n{cid_url}'
                    ).format(
                        name=obj.name,
                        address=obj.address,
                        phone=obj.phone_number,
                        url=obj.url,
                        cid_url=obj.cid_url
                    ),
                    description=obj.description,
                    directions=obj.directions,
                    related_searches=obj.related_keywords
                )
                writer.writerow(data)

        file.close()
