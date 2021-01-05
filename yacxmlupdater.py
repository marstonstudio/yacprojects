#!/usr/bin/python3

import logging
import argparse
import sqlite3
import zipfile
from xml.dom import minidom
import os

class Updater:

    def __init__(self, library, id, max):
        formatter = logging.Formatter('%(asctime)s - %(levelname)s ---------- %(message)s', '%Y-%m-%d %H:%M:%S')
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        self.logger = logging.getLogger('Updater')
        self.logger.addHandler(console)
        self.logger.setLevel(logging.INFO)

        self.library_root_path = os.path.abspath(library)
        self.db_path = os.path.join(self.library_root_path, ".yacreaderlibrary" + os.sep + "library.ydb")
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_cursor = self.db_conn.cursor()
       
        self.id_init = id
        self.max_count_to_process = max

    def main(self):
        self.logger.info('running updater on database at %s starting at comic_info_id:%i with max records:%i', self.db_path, self.id_init, self.max_count_to_process)

        id_current = self.id_init
        count_processed = 0
        
        self.db_cursor.execute("SELECT MAX(id) FROM comic_info;")
        id_max = self.db_cursor.fetchone()[0]
        self.logger.info('database highest comic_info_id:%i', id_max)

        if self.max_count_to_process == -1:
            self.db_cursor.execute("SELECT COUNT(*) FROM comic_info WHERE id >= :id;", {"id":self.id_init})
            count_max = self.db_cursor.fetchone()[0]
        else:
            count_max = self.max_count_to_process

        while id_current <= id_max and count_processed < count_max:

            self.db_cursor.execute("""
                SELECT ci.id, c.path, ci.volume, ci.number 
                FROM comic_info AS ci 
                JOIN comic AS c ON c.comicInfoId = ci.id 
                WHERE ci.id = :id;
            """, {"id":id_current})
            comic_row = self.db_cursor.fetchone()
            comic_record = ComicRecord(comic_row[0], comic_row[1], comic_row[2], comic_row[3])

            xml = self.extract_xml(comic_record.get_path())
            if not xml:
                self.logger.info("No xml data, skipping comic_info_id: %i, path: %s", comic_record.get_info_id(), comic_record.get_path())
            else:
                comic_data = ComicData(comic_record, xml)
                self.db_cursor.execute("""
                    UPDATE comic_info SET
                        title=:title,
                        number=:number,
                        count=:count,
                        volume=:volume,
                        genere=:genre,
                        writer=:writer,
                        penciller=:penciller,
                        inker=:inker,
                        colorist=:colorist,
                        letterer=:letterer,
                        coverArtist=:coverArtist,
                        date=:date,
                        publisher=:publisher,
                        synopsis=:synopsis,
                        characters=:characters,
                        comicVineID=:comicVineID
                    WHERE id=:id;
                    """, comic_data.get_object())
                self.db_conn.commit()
                count_processed += 1
                self.logger.info("Info updated %i of %i, comic_info id: %i, path: %s", count_processed, count_max, comic_record.get_info_id(), comic_record.get_path())

            id_current += 1
    
        self.db_cursor.close()

    def extract_xml(self, comic_path):
        zip_path = self.library_root_path + comic_path
        xml_file = None
        if zipfile.is_zipfile(zip_path) :
            with zipfile.ZipFile(zip_path) as cbz_file:
                if "ComicInfo.xml" in cbz_file.namelist() :
                    with cbz_file.open("ComicInfo.xml") as comic_xml_file:
                        xml_file = minidom.parse(comic_xml_file)
                        comic_xml_file.close()     
                cbz_file.close()
        return xml_file

class ComicRecord:

    def __init__(self, id, path, volume, number):
        self.id = id
        self.path = path
        self.volume = volume
        self.number = number

    def get_info_id(self):
        return self.id

    def get_path(self):
        return self.path

    def get_volume(self):
        return self.volume

    def get_number(self):
        return self.number

class ComicData:
    # https://gist.github.com/vaemendis/9f3ed374f215532d12bda3e812a130e6

    def __init__(self, record, xml):
        self.record = record
        self.xml = xml

    def parse_xml_string(self, xml_dom, element_name):
        element_list = xml_dom.getElementsByTagName(element_name)
        if len(element_list) > 0:
            return element_list[0].firstChild.data
        return None

    def get_record(self):
        return self.record

    def get_title(self):
        return self.parse_xml_string(self.xml, 'Title')

    def get_number(self):
        i = self.parse_xml_string(self.xml, 'Number')
        return int(i) if i is not None and i.isdigit() else None

    def get_count(self):
        i = self.parse_xml_string(self.xml, 'Count')
        return int(i) if i is not None and i.isdigit() else None
 
    def get_volume(self):
        return self.parse_xml_string(self.xml, 'Series')

    def get_genre(self):
        return self.parse_xml_string(self.xml, 'Genre')

    def get_writer(self):
        return self.parse_xml_string(self.xml, 'Writer')

    def get_penciller(self):
        return self.parse_xml_string(self.xml, 'Penciller')
    
    def get_inker(self):
        return self.parse_xml_string(self.xml, 'Inker')

    def get_colorist(self):
        return self.parse_xml_string(self.xml, 'Colorist')

    def get_letterer(self):
        return self.parse_xml_string(self.xml, 'Letterer')

    def get_cover_artist(self):
        return self.parse_xml_string(self.xml, 'CoverArtist')

    def get_date(self):
        month = self.parse_xml_string(self.xml, 'Month')
        year = self.parse_xml_string(self.xml, 'Year')
        if month is None or year is None:
            return None
        else:
            if len(month) == 1:
                month = "0" + month
            return "01/" + month + "/" + year

    def get_publisher(self):
        return self.parse_xml_string(self.xml, 'Publisher')

    def get_synopsis(self):
        return self.parse_xml_string(self.xml, 'Summary')

    def get_characters(self):
        comma_list = self.parse_xml_string(self.xml, 'Characters')
        if comma_list :
            return comma_list.replace(", ", "\n")

    def get_vine_id(self):
        web = self.parse_xml_string(self.xml, 'Web') #http://www.comicvine.com/iron-fist-1-a-duel-of-iron/4000-15784/
        if web:
            split_web = web.rsplit("-", maxsplit=1)
            if len(split_web) == 2:
                return split_web[1].replace("/", "")
        return None 

    def get_object(self):
        return { \
            "title": self.get_title(), \
            "number": self.get_number(), \
            "count": self.get_count(), \
            "volume": self.get_volume(), \
            "genre": self.get_genre(), \
            "writer": self.get_writer(), \
            "penciller": self.get_penciller(), \
            "inker": self.get_inker(), \
            "colorist": self.get_colorist(), \
            "letterer": self.get_letterer(), \
            "coverArtist": self.get_cover_artist(), \
            "date": self.get_date(), \
            "publisher": self.get_publisher(), \
            "synopsis": self.get_synopsis(), \
            "characters": self.get_characters(), \
            "comicVineID": self.get_vine_id(), \
            "id": self.get_record().get_info_id()
        }

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Update yac db with ComicRack xml data contained in cbz files')
    parser.add_argument('--library', nargs='?', default='.', type=str, help='path to yac library where .yacreaderlibrary/library.ydb resides')
    parser.add_argument('--id', nargs='?', default=1, type=int, help='yac comic_info id to resume updating at, defaults to 1')
    parser.add_argument('--max', nargs='?', default=-1, type=int, help='maximum number of issues to process, defaults to no limit')
    args = parser.parse_args()

    updater = Updater(args.library, args.id, args.max)
    updater.main()