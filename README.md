### Cloning the repository

--> Clone the repository using the command below :
```bash
https://github.com/trtuananh/trainpal_dj.git

```

### Setup environment

--> Install Miniconda :
You can download the .exe file to install Miniconda on Windows here https://docs.anaconda.com/miniconda/miniconda-install/. 
After installing Miniconda, open the Anaconda Prompt to create a new environment using the command:


```bash
conda create --name trainpal_dj python=3.10.6

```
Activate the Miniconda environment using the command.

```bash
conda activate trainpal_dj

```

--> Install the requirements :
Navigate to the project directory (...\trainpal_dj) in the Conda Prompt to proceed with installing Python requirements. 
Run the command to install python requirements:

```bash
pip install -r requirements.txt

```

#

### Running the server

--> Run the server using:
```bash
python manage.py runserver

```

> Then, the backend server will be started at http://127.0.0.1:8000/
