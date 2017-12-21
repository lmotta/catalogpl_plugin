<!-- PlanetLab-->
[planetlab_logo]: https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Planet_logo_New.png/240px-Planet_logo_New.png

![][planetlab_logo]
[PlanetLab](https://www.planet.com/explorers/)

# Catalog Planet Lab Plugin QGIS

This plugin lets you get images from the Planet Labs API(Version 1),
by performing searches for images that intersect with the extent of the map window.
It is a product from Planet Explorers program (https://www.planet.com/explorers/),
it is not an official Planet Labs's plugin.
You need a key from Planet Labs in order to use this plugin.
This plugin will be create polygon layer (Catalog of images) from intersect with the extent of the map window.
With this plugin, you can download full images(Analytic, UDM, ...), thumbnail images or
add TMS images.
See presentation: https://www.slideshare.net/LuizMotta3/catalog-planet-labs-plugin-for-qgis-v1
Tested with QGIS 2.18.13

## Author
Luiz Motta

## Changelog
- 2017-12-20
Fixed error ltgRoot in downloadImages(catalogpl.py).
- 2017-11-12
Change menus, catalog group, scene layer, count total dates. Fixed use in Windows
- 2017-10-06
Add groups of images with same date,
add menu Open Form in images, clear cache of TMS, and
add action 'Add selection' to pl_scenes
- 2017-10-04
Reverse images order in group catalog, add directories,
tms, tif, thumbnail, inside download directory 
- 2017-10-03
Fix cache_path when save TMS
- 2017-10-02
Change TMS by Server tiler XYZ to GDAL_WMS
Fixed when the first use of plugin(not set the directory), not show the setting
- 2017-10-01
Changed checkbox to radiobutton for images, only one type of image for searching.
- 2017-09-30
Updated to API Planet V1
- 2015-08-17
Fixed message when error download and add message log
- 2015-7-28
Add context menu remove key
- 2015-07-15
Add context menu image full and TMS
- 2015-07-12
Update the checkLayerLegend(), remove clean register
- 2015-07-09
Add cancel for TMS for download
- 2015-07-07
Add TMS for download
- 2015-06-12:
Add feature for download images and thumbnails
Add metadata in table and refactoring codes.
- 2015-04-26:
Create plugin.
