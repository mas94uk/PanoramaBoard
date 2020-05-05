#!/bin/bash

# Find possible panorama photos, being defined as those whose width is more
# than double their height, whose height is more than double their width.

if [[ 2 -ne $# ]]; then
    NAME=`basename $0`
    echo -e "\n$NAME: Find panorama pictures"
    echo -e "Usage:"
    echo -e "  $NAME <sourcepath> <destpath>\n"
    exit 1
fi

SOURCEPATH=$1
if [[ ! -d "$SOURCEPATH" ]]; then
    echo "Source path $SOURCEPATH does not exist."
    exit 2
fi

DESTPATH=$2
if [[ ! -d "$DESTPATH" ]]; then
    echo "Destination path $DESTPATH does not exist."
    exit 4
fi

find "$SOURCEPATH" -iregex ".*\\.jpe?g" | while read SOURCEFILE; do
    # Get the size of the file: identify prints a load of stuff, including the size.
    # Put this into an array, with element 0 being the width, 1 being the height. 
    arr=(`identify "$SOURCEFILE" | tr " " "\n" | grep -P "^\d{3,}x\d{3,}$" | tr "x" " "`)
    if [[ 2 -eq ${#arr[@]} ]]; then
        X=${arr[0]}
        Y=${arr[1]}
        
        # If the length is more than double the width, or the width is more than double the height
        MIN=$(($X>$Y?$Y:$X))
        MAX=$(($X<$Y?$Y:$X))
        echo "$X x $Y - $SOURCEFILE"
        if [[ $MAX -gt $(($MIN*2)) ]]; then
            echo -e "This is a panorama!\n"
            NAME=`echo "$SOURCEFILE" | tr "/" "_"`
            DESTFILE=${DESTPATH}/$NAME
            cp -a "$SOURCEFILE" "$DESTFILE" 
        fi
    fi
done

echo $SOURCEFILES
