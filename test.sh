if [ ! -d "venv" ] 
then
    echo "venv not present. Creating" 
    bash common/bash/dependencies.sh
    chmod -R 775 venv
fi

source "./venv/bin/activate"


python3 test.py $1 2>&1 | tee ./test.log