import os,sys,math

import viframework
import vianimator 
def launch_command():
  try:
    vianimator.api.SetGuiStyleCmd('dark').execute()
  except:
    pass
  # constants
  DTOR = math.pi/180.0
  RTOD = 180.0 / math.pi
  # add model
  vianimator.api.SetWorkingDirectoryCmd('C:/Users/amp20/Desktop/Formula/CFR27/22/Virtual Formula/Working_Directory').execute()
  vdb = viframework.viutils.VIDB()
  success = vdb.parse('vicrt_cdb.cfg')
  scene_manager = viframework.viosgobjects.SceneManager()
  analysis_manager = viframework.viobjects.simulation.AnalysisManager()
  try:
    vianimator.api.LoadModelCmd('C:/Users/amp20/Desktop/Formula/CFR27/22/Virtual Formula/Working_Directory/CFR25_swe_graphics.xgr').execute()
  except:
    pass
  try:
    vianimator.api.LoadModelCmd('C:/Users/amp20/Desktop/Formula/CFR27/22/Virtual Formula/Working_Directory/CFR25_swe_road_graphics.xgr').execute()
  except:
    pass
  vianimator.api.LoadModelCmd('C:/Program Files/VI-grade/VI-CarRealTime 2025/acarrt/carrealtime_shared.cdb/graphic_models.tbl/tireforces.xgr').execute()
  vianimator.api.LoadModelCmd('C:/Program Files/VI-grade/VI-CarRealTime 2025/acarrt/carrealtime_shared.cdb/graphic_models.tbl/widgets.xgr').execute()
  
  models = scene_manager.getGraphicModels()
  modelName = models[0].getName()
  vianimator.api.LoadPlotConfigurationCmd('C:/Program Files/VI-grade/VI-CarRealTime 2025/acarrt/carrealtime_shared.cdb/plot_configs.tbl/vi_animator_std.xpl').execute()
  vianimator.api.SocketStartCmd('127.0.0.1', 22222, modelName ).execute()
  vianimator.api.FollowModelCmd(modelName).execute()
  for model in models:
    modNam=model.getName()
    scene_manager.getGraphicModel(modNam).setAnalysis(analysis_manager.getAnalysis(modelName))
  viframework.viobjects.simulation.Analysis.setSourceFile(analysis_manager.getAnalysis(modelName),'CFR25_swe.res')
launch_command()

