#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh



RAWCONFIG=$(mktemp /tmp/tg2_generator_filepayload_XXXXXX)
echo "{ 0, 1, 2, 3 }" > $RAWCONFIG



run_and_display RawConfig --num 1 --filename ${RAWCONFIG}
cat ${TESTID_FILE_DISPLAYED}



check_value "Raw.load: b'\\\\x00\\\\x01\\\\x02\\\\x03'"



rm -f ${RAWCONFIG}
cleanup
rreturn 0 "$0"
