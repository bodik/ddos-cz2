#!/bin/sh

. $(dirname $(readlink -f $0))/common.sh



TESTPAYLOAD=$(mktemp /tmp/tg2_generator_filepayload_XXXXXX)
echo "0,0,0,0,0,0,0,0,0,0" > $TESTPAYLOAD



run_one_and_display EthernetFilePayload --eth_protocol "0x0000" --filename ${TESTPAYLOAD}
cat ${TESTID_FILE_DISPLAYED}



check_value "802.3.len: 0"



rm -f ${TESTPAYLOAD}
cleanup
rreturn 0 "$0"
