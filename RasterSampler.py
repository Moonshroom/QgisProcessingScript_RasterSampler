# -*- coding: utf-8 -*-
#Mateusz Orylski Geoinformatyka Programowanie Geoinformacyjne ZADANIE ZALICZENIOWE NR. 1
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QSize
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterMapLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFeatureSink,
                       QgsVectorLayer,
                       QgsRasterLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProject,
                       QgsMapSettings,
                       QgsRectangle,
                       QgsMapRendererSequentialJob)
from qgis import processing
import numpy as np
import random
from osgeo import gdal

class RasterSampler(QgsProcessingAlgorithm):

    INPUT = 'INPUT' #Wczytany raster - path
    NUMBEROFPOINTS = 'NUMBEROFPOINTS' #Ilość punktów
    SIZE = 'SIZE' #Wielkośc próbki
    OUTPUT = 'OUTPUT' #Miejsce zapisu

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RasterSampler()

    def name(self):
        return 'RasterSampler'

    def displayName(self):
        return self.tr('Raster Sampler')

    def group(self):
        return self.tr('Geoinformatyka_rok_1_Mateusz_Orylski')

    def groupId(self):
        return 'PRGGEO'

    def shortHelpString(self):
        return self.tr("Generate random samples from raster input." +
        " " + "INPUT must be an existing layer." + " " + "Set OUTPUT folder directory")
       
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.INPUT,
                self.tr('Input raster (INPUT must be an existing layer)'),
                [QgsProcessing.TypeRaster]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NUMBEROFPOINTS,
                self.tr('Number of sampels'),
                defaultValue = 10
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SIZE,
                self.tr('Sample size'),
                defaultValue = 32
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                self.tr('Choose folder directory for outputs file')
            )
        )
        
    def processParameters(self,parameters,context,feedback):
        
        rasterSource = self.parameterAsLayer(
            parameters,
            self.INPUT,
            context
        )
        if rasterSource is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
   
        sampleSize = self.parameterAsDouble(
            parameters,
            self.SIZE,
            context)

        numberOfPoints = self.parameterAsInt(
            parameters,
            self.NUMBEROFPOINTS,
            context)
        
        folderDestination = self.parameterAsString(
            parameters,
            self.OUTPUT,
            context)
        
        
        
        self.INPUT = rasterSource
        self.SIZE = sampleSize
        self.NUMBEROFPOINTS = numberOfPoints
        self.OUTPUT = folderDestination
       
    def processAlgorithm(self, parameters, context, feedback):
        #Parametry
        self.processParameters(parameters, context, feedback)
        rasterPath = self.INPUT
        size = self.SIZE
        numberPoints = self.NUMBEROFPOINTS
        folderoutput = self.OUTPUT
        #Wczytanie rastra
        rLayer = rasterPath
        #Wyznaczenie granic rastra
        ext = rLayer.extent()
        (xmin, xmax, ymin, ymax) = (ext.xMinimum(), ext.xMaximum(), ext.yMinimum(), ext.yMaximum())
        #Funkcja do generowania losowych punktów w obrębie rastra
        def create_points(number):
            points = []
            for i in range(number):
                point = np.random.uniform(xmin,xmax), np.random.uniform(ymin,ymax)
                points.append(point)
            np.array(points)
            return points  
        #Tworzenie punktów    
        pLayer = QgsVectorLayer('Point?crs=epsg:2180&field=id:int', 'points' , 'memory')
        prov = pLayer.dataProvider()
                 
        points = create_points(numberPoints)
        feats = []
        ID = 1
        for point in points:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*point)))
            feat.setAttributes([ID,'id'])
            ID += 1
            feats.append(feat)
        prov.addFeatures(feats)
        pLayer.updateExtents()
        
        #Próbkowanie rastra
        def sampling(pLayer,rLayer):
                        
            nameFile= "mapsampel_" #nazwa rastra wynikowego
            type= "png" #format pliku rastra wynikowego
            where_ = folderoutput #ścieżka do folderu w którym mają się zapisać rastry
            player= pLayer  #warstwa wektorowa - punkty
            rlayer= rLayer  #warstwa rastrowa - input

            registry = QgsProject.instance()
            #Zablokowane / zakomentowane wyświetlanie warstw
            '''
            registry.addMapLayer(rlayer)
            registry.addMapLayer(player)
            '''
            registry.mapLayers().keys()
            
            #rozmiar obszaru 
            xs=rlayer.rasterUnitsPerPixelX()*size/2
            ys=rlayer.rasterUnitsPerPixelY()*size/2

            options = QgsMapSettings()
            options.setLayers([rlayer]) 
            options.setOutputSize(QSize(xs, ys)) 
            
            points=player.getFeatures()
            for i,point in enumerate(points):
                pt=point.geometry().asPoint()
                ext=QgsRectangle(pt[0]-xs,pt[1]-ys,pt[0]+xs,pt[1]+ys)
                options.setExtent(ext) #3
                render = QgsMapRendererSequentialJob(options)
                render.start()
                render.waitForFinished()
                name = "{}\{}_{}.{}".format(where_,nameFile,str(i),type)
                img = render.renderedImage()
                img.save(name, type)
        sampling(pLayer, rLayer)
        return {'Check Your OUTPUT folder directory, SUCCESS': True }
