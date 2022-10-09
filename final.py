from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsField,
                       QgsProject,
                       QgsRasterLayer,
                       QgsRasterBandStats,
                       QgsColorRampShader,
                       QgsPalettedRasterRenderer)
from qgis import processing
#from PyQt5.QtCore import *
from PyQt5.QtGui import (QColor)
#from qgis.utils import *
from qgis.analysis import (QgsRasterCalculatorEntry,QgsRasterCalculator)


class ChangeDetectionAlgorithm(QgsProcessingAlgorithm):
    

    INPUT1 = 'INPUT1'
    INPUT2 = 'INPUT2'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ChangeDetectionAlgorithm()

    def name(self):
        
        return 'Change Detection'

    def displayName(self):
       
        return self.tr('Change Detection Analysis')

    def group(self):
      
        return self.tr('Example scripts')

    def groupId(self):
      
        return 'examplescripts'

    def shortHelpString(self):
        
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
       
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT1, self.tr('Input Before Image'), [QgsProcessing.TypeRaster]))
        
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT2, self.tr('Input After Image'), [QgsProcessing.TypeRaster]))
    
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Change Detection Layer'),QgsProcessing.TypeRaster))
   
    def processAlgorithm(self, parameters, context, feedback):
        input1 = self.parameterAsRasterLayer(parameters, self.INPUT1, context)
        if input1 is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))#FEEDBACK TO USER TO GIVE AN INPUT 
            
        input2 = self.parameterAsRasterLayer(parameters, self.INPUT2, context)
        if input2 is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))#FEEDBACK TO USER TO GIVE AN INPUT 
       
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        def ndvi(input):
            #NDVI 1
            rasterName = "input"
            raster = input
            ir = QgsRasterCalculatorEntry()
            r = QgsRasterCalculatorEntry()
            ir.raster = raster
            r.raster = raster
            ir.bandNumber = 5
            r.bandNumber = 4
            ir.ref = rasterName + "@5"
            r.ref = rasterName + "@4"
            references = (ir.ref, r.ref, ir.ref, r.ref)
            exp = "1.0 * (%s - %s) / 1.0 + (%s + %s)" % references

            e = raster.extent()
            w = raster.width()
            h = raster.height()
            entries = [ir,r]
            ndvi = QgsRasterCalculator(exp, 'TEMPORARY_OUTPUT', "GTiff", e, w, h, entries)
            ndvi.processCalculation()
            lyr = QgsRasterLayer('TEMPORARY_OUTPUT', "NDVI")
            

                   
            raster_provider = lyr.dataProvider()
            stats = raster_provider.bandStatistics(1, QgsRasterBandStats.All)
          
            pos_two = (stats.maximumValue)
            pos_three = (stats.minimumValue)
                   
                    
            table_list = ['7000',pos_two,1,pos_three,'7000',2]
                    
            #reclassify 
            aspectReclassDict = {'INPUT_RASTER' : lyr,
                                 'RASTER_BAND' : 1,
                                 'TABLE' : table_list,
                                 'NO_DATA' : -9999,
                                 'RANGE_BOUNDARIES' : 0,
                                 'NODATA_FOR_MISSING' : False,
                                 'DATA_TYPE' : 5,
                                 'OUTPUT' : 'TEMPORARY_OUTPUT'}

            aspectReclass = processing.run("qgis:reclassifybytable", aspectReclassDict)
                    
            reclassLyr = QgsRasterLayer(aspectReclass['OUTPUT'])
            return(reclassLyr)
            
        beforeName = "Before" 
        afterName = "After"  
        beforeRaster = ndvi(input1)
        afterRaster = ndvi(input2)

        #QgsProject.instance().addMapLayer(beforeRaster)
        #QgsProject.instance().addMapLayer(afterRaster)

        beforeEntry = QgsRasterCalculatorEntry() 
        afterEntry = QgsRasterCalculatorEntry() 
        beforeEntry.raster = beforeRaster 
        afterEntry.raster = afterRaster 
        beforeEntry.bandNumber = 1 
        afterEntry.bandNumber = 1 
        beforeEntry.ref = beforeName + "@1" 
        afterEntry.ref = afterName + "@1" 
        entries = [afterEntry, beforeEntry]

        exp = "%s - %s" % (afterEntry.ref, beforeEntry.ref) 

        #filepath = "C:\\Users\\gangul\\Downloads\\data Programming\\"

        e = beforeRaster.extent() 
        w = beforeRaster.width() 
        h = beforeRaster.height() 

        change = QgsRasterCalculator(exp, output, "GTiff", e, w, h, entries) 
        change.processCalculation() 

        lyr2 = QgsRasterLayer(output, "Change") 

        stats = lyr2.dataProvider().bandStatistics(1, QgsRasterBandStats.All)

        min = stats.minimumValue
        max = stats.maximumValue

        pcolor = []

        pcolor.append(QgsColorRampShader.ColorRampItem(-986, QColor("#d2ca97"), '-986'))    
        pcolor.append(QgsColorRampShader.ColorRampItem(-1, QColor("#ff0101"), 'Forest Loss'))    
        pcolor.append(QgsColorRampShader.ColorRampItem(0, QColor("#a1d99b"), 'No change'))    
        pcolor.append(QgsColorRampShader.ColorRampItem(1, QColor("#1201ff"), 'Forest Gain'))    
        pcolor.append(QgsColorRampShader.ColorRampItem(253, QColor("#006d2c"), '253'))    

        renderer = QgsPalettedRasterRenderer(lyr2.dataProvider(), 1, QgsPalettedRasterRenderer.colorTableToClassData(pcolor))
        lyr2.setRenderer(renderer)
        lyr2.triggerRepaint()
        QgsProject.instance().addMapLayer(lyr2)
        return {}
