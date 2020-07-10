
#grep -B1 -A5 NOVA xmlguide.xmltv

#2019_02_15_15_30_00

IFS=$'\n'

for episodeFile in $(find /srv/media/dvr/ -type f -name '*.ts')
do
	#echo $episodeFile
	mainTitle=$(echo $episodeFile | awk -F/ '{print $5}')
	#echo $mainTitle
	episodeTitle=$(echo $episodeFile | awk -F/ '{print $6}')
	#echo $episodeTitle
	titlePart=$(echo $episodeTitle | awk -F- '{print $1}')
	datePart=$(echo $titlePart | awk 'NF>1{print $NF}')
	datePart=$(echo $datePart | awk -F. '{print $1}')
	datePart=$(echo $datePart | sed 's/_//g')
	#echo $datePart

	grep -B1 -A5 -i $mainTitle xmlguide.xmltv | grep $datePart
	res=$?
	if [ $res -eq 0 ]
	then
		echo "Found Guide data for $episodeTitle"
		guideData=$(grep -B1 -A5 -i $mainTitle xmlguide.xmltv | grep -A6 $datePart)
		echo $guideData
		TODO: Seperate episode SXXEXX line in scraper and use to rename
	fi
	echo ""
	echo ""
	echo ""
done
