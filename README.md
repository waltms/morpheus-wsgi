# Morpheus with WSGI

This is a short and simple WSGI web interface for Morpheus as currently maintained by [The Perseids Project](https://www.perseids.org/). In order to use this, you will need a running copy of Morpheus, which can be compiled from source found [here](https://github.com/perseids-tools/morpheus). 

>[!IMPORTANT]
>If you get a fatal compile error relating to the `gets()` function in `deverb.c`, then you will need to fix line 26 of `src/anal/deverb.c` by replacing it with
>
>```c
>while(fgets(line, sizeof(line), stdin)) {
>```

## Requirements

Install the Python3 package `beta-code`

```python
sudo pip3 install beta_code
```

>[!IMPORTANT]
>Before you continue, you will need to fix the Python `beta_code` package because it is currently broken out of the box, at least for Python <= 3.12. On lines 8 and 11 of `/usr/local/lib/python3.12/site-packages/beta_code/beta_code.py` you will need to specify `encoding='utf-8'` in the `open()` call or the package load will crash with an ascii error.

## Installation

 - Your webserver must have WSGI enabled. In the appropriate web directory (e.g. `/var/www/wsgi/morpheus/`) copy your entire Morpheus install contents.
 - Copy `morpheus.py` and `morpheus.html` from this repository into the same directory.
 - Add the following directives into your webserver config file:

```apacheconf
    <Directory "/var/www/wsgi/morpheus">
        Require all granted
    </Directory>

    WSGIDaemonProcess morpheus \
    python-path=/usr/lib/python3.12/site-packages:/usr/local/lib/python3.12/site-packages

    WSGIScriptAlias /morpheus /var/www/wsgi/morpheus/morpheus.py
```

>[!IMPORTANT]
>Make sure that the `python-path` in your `WSGIDaemonProcess` directive has the correct paths to both your base and local packages.

 - Restart your webserver.

## Usage

The web interface should now be usable as: `https://my-web-site/morpheus?word=πόλις`

By adding `&input=1` (`https://my-web-site/morpheus?word=πόλις&input=1`) to the URL, the interface will add a search box at the top, so that you don't need to need to change the URL for each new search.

>[!TIP]
>If you don't want to use UTF-8 Greek to do searches, you can use betacode instead.

The results have a somewhat more readable format than the default `morpheus` output, including use of UTF-8 Greek.

>[!NOTE]
>Lemmas have a link to the corresponding entries in [Logeion](https://logeion.uchicago.edu/).

>[!TIP]
>In `morpheus.py` there are two variables worthy of being mentioned. One is `acceptable_referers`, a list of acceptable referers, in case you would like the interface to only be accessible from a pre-designated website link. This functionality will only be enforced if the variable `need_referer` is set to `True`.
