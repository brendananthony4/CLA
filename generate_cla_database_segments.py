import time
import unicodecsv as csv
import sys
import glob
import os

def import_csv(infile):
    """
    Return raw data array from csv file.

    Parameters
    ----------
    infile : name of csv file to read.
    """
    if not os.path.isfile(infile):
        sys.exit('>> No input file named {} found'.format(infile))
    else:
        return [line for line in csv.reader(open(infile,'rU'), delimiter='\t')]

def write_unique_points(d, inf_name):
    """
    
    """

    def is_in(existing, c):
        match = False
        if len(existing) > 0:
            for r in existing:
                if r[0:3] == c[0:3]:
                    match = True
        return match

    with open(os.path.join(inf_name+' Points.csv'),'w') as outf:
        print '>> Writing Unique Points...',
        writer = csv.writer(outf)
        writer.writerow(['ID','Library or Archive','City or Region','Country',
                         'Centroid Type', 'Latitude', 'Longitude', 'WKT String'])
        data_to_write = []
        for row in d:
            #print len(row)
            try:
                if row[8] != '' and row[9] != '':
                    wkt_point = ['POINT({0} {1})'.format(row[9], row[8])]
                    node_line = row[1:5] + row[8:10] + wkt_point
                    data_to_write.append(node_line)
            except IndexError:
                pass
            except UnicodeEncodeError:
                print row
                raise
        unique_rows = []

        for row in data_to_write:
            if not is_in(unique_rows, row):
                unique_rows.append(row)
        for idx, row in enumerate(unique_rows):
            row.insert(0, str(idx))
        writer.writerows(unique_rows)  
        print 'Got {0} points'.format(len(unique_rows))

def write_all_points(denormalized_data):
    """
    Write a complete list of points attested for all manuscripts,
    including one row for each MS-place (i.e. points are not spatially
    unique) where a Lat/Long pair have been identified.

    Parameters
    ----------
    denormalized_data : 
    """
    print '>> Writing All Manuscript-Points...',
    with open('all_points.csv','w') as outf:
        writer = csv.writer(outf)
        writer.writerow(['ID', 'Library or Archive', 'City or Region', 
            'Country', 'Centroid Type', 'Certainty', 'Blank?', 'Relation', 
            'Latitude', 'Longitude', 'Order', 'Text', 'Start Date', 'End Date', 
            'Date Q', 'Date Literal', 'Notes', 'WKT String'])
        full_rows = [[field[0:254] for field in d] for d in denormalized_data if d[8]!= '' and d[9] != '']
        for row in full_rows:
            writer.writerow(row + ['POINT({0} {1})'.format(row[9], row[8])])
    print 'Got {0} total points'.format(len(full_rows))

def denormalize_dataset(raw_data, inf_name):
    """
    Return one manuscript point per line.
    """
    # denormalize rows
    denormalized_data = []
    for row in raw_data:
        # add place copied
        place_copied = [row[1], row[36], row[37], row[38], row[40], row[39],
                        row[49], row[50], row[41], row[42], row[51], '',
                        row[17], row[18], '', '','']
        denormalized_data.append(place_copied)

        # put in intermediate stages
        for x in xrange(58, len(row), 16):
            constr = []
            constr.append(row[1])
            for item in row[x:x+16]:
                constr.append(item)
            denormalized_data.append(constr)

        # put current library
        current_library = [row[1], row[4], row[5], row[6], '', '', row[9],
                           'Current', row[7], row[8], row[10], '', '', '',
                           '', '', '']
        denormalized_data.append(current_library)

    write_unique_points(denormalized_data, inf_name)
    denorm_copy = denormalized_data[:]
    #write_all_points(list(denorm_copy))
    return denormalized_data

def write_output(final_data, outfile):
    """
    Write line segments to CSV file
    """
    with open(outfile, 'w') as outf:
        csv.writer(outf).writerows(final_data)

def write_truncated_output(final_data, outfile):
    """
    Write line segments to CSV file
    """
    with open(outfile, 'w') as outf:
        csv.writer(outf).writerows([[item[0:254] for item in row] for row in final_data])

def add_wkt_lines(database):
    database[0].append('WKT')
    for row in database[1:]:
        row.append('LINESTRING({0} {1}, {2} {3})'.format(row[9], row[8], row[26], row[25]))
    return database

## Classes
class Manuscript(object):
    def __init__(self, movements, ms_number):
        self.data = movements
        self.uid = ms_number
        self.segments = []

    def __repr__(self):
        return 'Processing CLA ID {0}'.format(self.uid)

    def parse_manuscript_record(self):
        #for row in self.data: print row[0], row[8]f
        self.data.sort(key = lambda row:row[10])
        # find first point-event that isn't coded 'd' or 'f' or 'm'
        i = 0
        try:
            while self.data[i][6] in ['d','f','m']:
                i += 1
            last_ok_point = self.data[i]
        # if no point not coded d or f is found
        except IndexError:
            return False

        for x in xrange(0, len(self.data)):
            if self.data[x] != last_ok_point:
                if self.data[x][6] in ['d','f','m']:
                    seg = self.data[x] + last_ok_point
                else:
                    seg = last_ok_point + self.data[x]
                    last_ok_point = self.data[x]

                self.segments.append(seg)
        # return bool to evaluate whether there are valid segments
        return True if len(self.segments) > 0 else False

def process_cla_volume(infile, mode = 'csv'):
    if mode == 'csv':
        raw_data = import_csv(infile)[1:]
    elif mode == 'excel':
        raw_data = import_excel(infile)[1:]
    #print '>> Denormalizing dataset'
    denormalized_data = denormalize_dataset(raw_data, infile[:-4]) 
    #for d in denormalized_data: print len(d)
    headers = ['FR_MSID', 'FR_Library', 'FR_City', 'FR_Country', 'FR_Centroid',
               'FR_Certainty', 'FR_Context', 'FR_Relation', 'FR_Latitude', 
               'FR_Longitude', 'FR_Order', 'FR_Text', 'FR_Start', 'FR_End',
               'FR_DateQ', 'FR_DateLit', 'FR_Comment', 'TO_MSID', 'TO_Library',
               'TO_City', 'TO_Country', 'TO_Centroid', 'TO_Certainty',
               'TO_Context', 'TO_Relation', 'TO_Latitude', 'TO_Longitude', 
               'TO_Order', 'TO_Text', 'TO_Start', 'TO_End', 'TO_DateQ',
               'TO_DateLit', 'TO_Comment']
    
    # exclude rows without two coordinate pairs
    valid_data = [x for x in denormalized_data if x[8] != '' and x[9] != '']
    
    ms_movements = []
    print '>> Parsing Manuscript Records...',
    for ms in set([x[0] for x in valid_data]):
        #print ms
        m = Manuscript([p for p in valid_data if p[0] == ms], ms)
        if m.parse_manuscript_record():
            for segment in m.segments:
                #print segment
                ms_movements.append(segment)
    print 'COMPLETED'

    # add headers and write CSV file
    ms_movements.insert(0, headers)
    ms_movements = add_wkt_lines(ms_movements)
    write_all_points(denormalized_data)
    print '>> Writing Manuscript Movement File...',
    write_truncated_output(ms_movements, os.path.join(infile[:-4]+'_movements.csv'))
    print 'COMPLETED'

if __name__ == '__main__':
    process_cla_volume('Complete CLA Database.tsv', mode = 'csv')
