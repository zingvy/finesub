from __future__ import unicode_literals
import struct
import os
import xbmcvfs


def calc_file_hash(filepath):
    ''' Calculates the hash value of a movie.
        Edited from from OpenSubtitles's own examples:
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
        '''

    try:
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)

        f = xbmcvfs.File(filepath, "rb")

        filesize = f.size()
        filehash = filesize

        if filesize < 65536 * 2:
            raise Exception('SizeError: Minimum file size must be 120Kb')

        for x in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l_value, ) = struct.unpack(longlongformat, buffer)
            filehash += l_value
            filehash = filehash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        f.seek(max(0, filesize - 65536), 0)
        for x in range(65536 // bytesize):
            buffer = f.read(bytesize)
            (l_value, ) = struct.unpack(longlongformat, buffer)
            filehash += l_value
            filehash = filehash & 0xFFFFFFFFFFFFFFFF

        filehash = '%016x' % filehash
        return filesize, filehash
    except IOError:
        raise
    finally:
        f.close()
