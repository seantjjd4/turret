Turret
=============================

This is a python program control automatic turret with termal camera through Raspberry Pi

## Matirial
single-board computers : [Raspberry Pi 4 model b](https://piepie.com.tw/product/raspberry-pi-4-model-b-4gb)

Motors : [K-Power Hb200t * 2](https://www.made-in-china.com/showroom/servo-kyra/product-detailTyEQoAuWXwhO/China-K-Power-Hb200t-12V-200kg-Torque-Steel-Gear-Digital-Industrial-Servo.html)

Thermal Camera: [MLX90640-BAA IR Thermal Camera](https://twarm.com/commerce/product_info.php?products_id=7218)

## Raspberry Pi Setup
[How to set up a Raspberry Pi](https://www.raspberrypi.com/tutorials/how-to-set-up-raspberry-pi/)


## Installation

  ### Using `pip`
  Use the package manager [pip](https://pip.pypa.io/en/stable/) to install python package.
  Install the dependencies from `requirements.txt`
  
  ```bash
  pip install
  ```
  
  If the `requirements.txt` not found or outdated, you may have to use `pipenv`

  ### Using `pipenv`
  Using Python virtualenv management tool [pipenv](https://pipenv.pypa.io/en/latest/) to install and isolate python packages from other projects.
  
  > To install `pipenv`
  > ```bash
  > pip install --user pipenv
  > ```
  
  Install the dependencies from `pipfile`
  
  ```bash
  pipenv install
  ```
  Install the dependencies from `requirements.txt`
  ```bash
  pipenv install -r path/to/requirements.txt
  ```
  
  If the `requirements.txt` not found or outdated, you may recreate it with `pipfile` from  `pipenv`:
  ```bash
  pipenv lock -r > requirements.txt
  ```
  ### Error installing opencv-python
  Sometime opencv-python couldn't be installed on Raspberry Pi. The installation will stuck in likely the last step, pending something forever.
  In this case, you may install the older version of opencv-python.
  e.g.:
  ```bash
  pip install opencv-python==4.4.0.46
  ```
  ### Adafruit_CircuitPython_MLX90640
  **Original Repository** : [Adafruit_CircuitPython_MLX90640](https://github.com/adafruit/Adafruit_CircuitPython_MLX90640.git)
  
  The original repository (python) is unable to use the frequency above 8 Hz with thermal camera.
  
  To make is work on 8 Hz and above, it is needed to make some changes in the original repository.
  
  **Edited Repository ( 8 Hz and above frequency enable )** : [Adafruit_CircuitPython_MLX90640](https://github.com/seantjjd4/Adafruit_CircuitPython_MLX90640.git)

  ```bash
  git clone https://github.com/seantjjd4/Adafruit_CircuitPython_MLX90640.git

  # in your project enviroment
  pip install -e /path/to/Adafruit_CircuitPython_MLX90640/
  
  ```

## Usage

```bash
cd /path/to/project_folder

python3 main.py
```
### To Run Test
```bash
python3 -m unittest

# to run specific test file
python3 -m unittest test/test_file
```
## Set Auto Start
There are serveral autostart methods in raspberry pi.
In this case, we are not interest about the user who login the system, so setting autostart using system method is quite appropriate.

```bash
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```
Add the command bellow at the last line of the file:
```bash
@python3 /path/to/project_folder/main.py
```
Restart and check the status!

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
