# SparkleBuilder
### a simple python script to automate [Sparkle](http://sparkle-project.org/) appcast generation and delta creation

#### basic instructions
* clone the repo
* `pip install requirements.txt`
* configure the settings in `sparkle-builder-config-example.json`
* rename the example to `sparkle-builder-config.json`
* configure the settings in `aws-s3-config-example.json`
* rename the example to `aws-s3-config.json`
* delete the file in `Builds/App`
* place your **latest** app in `Builds/App`
* cd into `Scripts`
* run `python sparkle-builder.py`

#### What it does (and can do)

* generates an appcast.xml file for use with [Sparkle](http://sparkle-project.org/).
* zips the application and signs with your private dsa key
* archives your app in a zip appending the version number
* archives your app appending the version number
* creates `delta` files for each pervious version of your app
* optionally
  * archives appcasts, deltas and zips
  * publishes the zips, appcast and deltas to another directory*

###### With everything enabled in the .config file your final directory structure will look like this:

* Builds/
  * App/
  * Appcast/
  * Archives/
    * Appcasts/
    * Apps/
    * Deltas/
    * Zips/
  * Deltas/
  * Zips/

###### The directory that you publish to will look like this:
* appcast/
* deltas/
* downloads/

##### Notes
* the appcast uses your build number aka `CFBundleVersion` in your info.plist for updates - make sure that it increments between versions!


>If you already have a bunch of builds, the recommendation is to create the `Builds/Archives/Apps/` folder and place each of the previous builds there *before* you run the app for the first time. Each app should be named with the version and build number appended to the file name.  So version 1.0.1 of your test.app should be named test-1.0.1.app

>Alternatively you could run the script for each version of your app starting at the lowest build number and going on from there
