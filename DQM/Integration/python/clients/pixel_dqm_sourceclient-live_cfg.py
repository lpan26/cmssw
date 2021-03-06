import FWCore.ParameterSet.Config as cms

from Configuration.StandardSequences.Eras import eras

process = cms.Process("PIXELDQMLIVE", eras.Run2_2017)

live=True  #set to false for lxplus offline testing
offlineTesting=not live

TAG ="PixelPhase1" 

process = cms.Process("PIXELDQMLIVE")

process.MessageLogger = cms.Service("MessageLogger",
    debugModules = cms.untracked.vstring('siPixelDigis',
                                         'siStripClusters', 
                                         'SiPixelRawDataErrorSource', 
                                         'SiPixelDigiSource'),
    cout = cms.untracked.PSet(threshold = cms.untracked.string('ERROR')),
    destinations = cms.untracked.vstring('cout')
)

#----------------------------
# Event Source
#-----------------------------
# for live online DQM in P5

if (live):
    process.load("DQM.Integration.config.inputsource_cfi")

# for testing in lxplus
elif(offlineTesting):
    process.load("DQM.Integration.config.fileinputsource_cfi")

#-----------------------------
# DQM Environment
#-----------------------------

process.load("DQMServices.Components.DQMEnvironment_cfi")

process.load("DQM.Integration.config.environment_cfi")

#----------------------------
# DQM Live Environment
#-----------------------------

process.dqmEnv.subSystemFolder = TAG
process.dqmSaver.tag = TAG


process.DQMStore.referenceFileName = '/dqmdata/dqm/reference/pixel_reference_pp.root'
if (process.runType.getRunType() == process.runType.hi_run):
    process.DQMStore.referenceFileName = '/dqmdata/dqm/reference/pixel_reference_hi.root'

if (process.runType.getRunType() == process.runType.cosmic_run):
    process.DQMStore.referenceFileName = '/dqmdata/dqm/reference/pixel_reference_cosmic.root'

#-----------------------------
# Magnetic Field
#-----------------------------

process.load('Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff')

#-------------------------------------------------
# GEOMETRY
#-------------------------------------------------

process.load("Configuration.StandardSequences.GeometryRecoDB_cff")

#-------------------------------------------------
# GLOBALTAG
#-------------------------------------------------
# Condition for P5 cluster

if (live):
    process.load("DQM.Integration.config.FrontierCondition_GT_cfi")

# Condition for lxplus: change and possibly customise the GT
elif(offlineTesting):
    process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
    from Configuration.AlCa.GlobalTag import GlobalTag as gtCustomise
    process.GlobalTag = gtCustomise(process.GlobalTag, 'auto:run2_data', '')

#-----------------------
#  Reconstruction Modules
#-----------------------

# Real data raw to digi
process.load("Configuration.StandardSequences.RawToDigi_Data_cff")
process.load("RecoLocalTracker.SiStripZeroSuppression.SiStripZeroSuppression_cfi")
process.load("RecoLocalTracker.SiStripClusterizer.SiStripClusterizer_RealData_cfi")

# PixelPhase1 Real data raw to digi
process.load("EventFilter.SiPixelRawToDigi.SiPixelRawToDigi_cfi")
process.siPixelDigis.IncludeErrors = True

process.siPixelDigis.InputLabel   = cms.InputTag("rawDataCollector")
process.siStripDigis.InputLabel   = cms.InputTag("rawDataCollector")

#--------------------------------
# Heavy Ion Configuration Changes
#--------------------------------

if (process.runType.getRunType() == process.runType.hi_run):    
    process.load('Configuration.StandardSequences.ReconstructionHeavyIons_cff')
    process.load('Configuration.StandardSequences.RawToDigi_Repacked_cff')
    process.siPixelDigis.InputLabel   = cms.InputTag("rawDataRepacker")

## Collision Reconstruction
process.load("Configuration.StandardSequences.RawToDigi_Data_cff")

## Cosmic Track Reconstruction
if (process.runType.getRunType() == process.runType.cosmic_run or process.runType.getRunType() == process.runType.cosmic_run_stage1):
    process.load("RecoTracker.Configuration.RecoTrackerP5_cff")
    process.load("Configuration.StandardSequences.ReconstructionCosmics_cff")

else:
    process.load("Configuration.StandardSequences.Reconstruction_cff")

import RecoVertex.BeamSpotProducer.BeamSpotOnline_cfi
process.offlineBeamSpot = RecoVertex.BeamSpotProducer.BeamSpotOnline_cfi.onlineBeamSpotProducer.clone()

process.load("DQM.SiPixelPhase1Config.SiPixelPhase1OnlineDQM_cff")

process.PerModule.enabled=True
process.PerReadout.enabled=True
process.OverlayCurvesForTiming.enabled=False
process.IsOffline.enabled=False


#import RecoVertex.BeamSpotProducer.BeamSpotOnline_cfi
#process.offlineBeamSpot = RecoVertex.BeamSpotProducer.BeamSpotOnline_cfi.onlineBeamSpotProducer.clone()

#--------------------------
# Service
#--------------------------
process.AdaptorConfig = cms.Service("AdaptorConfig")

#--------------------------
# Filters
#--------------------------

# HLT Filter
# 0=random, 1=physics, 2=calibration, 3=technical
process.hltTriggerTypeFilter = cms.EDFilter("HLTTriggerTypeFilter",
    SelectedTriggerType = cms.int32(1)
)

process.load('HLTrigger.HLTfilters.hltHighLevel_cfi')
process.hltHighLevel.HLTPaths = cms.vstring( 'HLT_ZeroBias_*' , 'HLT_ZeroBias1_*' , 'HLT_PAZeroBias_*' , 'HLT_PAZeroBias1_*', 'HLT_PAL1MinimumBiasHF_OR_SinglePixelTrack_*')
process.hltHighLevel.andOr = cms.bool(True)
process.hltHighLevel.throw =  cms.bool(False)

#--------------------------
# Scheduling
#--------------------------

process.DQMmodules = cms.Sequence(process.dqmEnv*
                                  process.dqmSaver)


### COSMIC RUN SETTING
if (process.runType.getRunType() == process.runType.cosmic_run or process.runType.getRunType() == process.runType.cosmic_run_stage1):
        
    # Reco for cosmic data
    process.load('RecoTracker.SpecialSeedGenerators.SimpleCosmicBONSeeder_cfi')
    process.simpleCosmicBONSeeds.ClusterCheckPSet.MaxNumberOfCosmicClusters = 450
    process.combinatorialcosmicseedfinderP5.MaxNumberOfCosmicClusters = 450

    process.RecoForDQM_TrkReco_cosmic = cms.Sequence(process.offlineBeamSpot*process.MeasurementTrackerEvent*process.tracksP5)
    
    process.p = cms.Path(
                         ##### TRIGGER SELECTION #####
                         process.hltHighLevel*
                         process.scalersRawToDigi*
                         process.APVPhases*
                         process.consecutiveHEs*
                         process.hltTriggerTypeFilter*
                         process.RecoForDQM_LocalReco*
                         process.DQMCommon*
                         process.RecoForDQM_TrkReco_cosmic*
                         process.siPixelPhase1OnlineDQM_source_cosmics*
                         process.siPixelPhase1OnlineDQM_harvesting
                         )
   
### pp COLLISION SETTING

if (process.runType.getRunType() == process.runType.pp_run or process.runType.getRunType() == process.runType.pp_run_stage1):
    # Reco for pp collisions
    process.load('RecoTracker.IterativeTracking.InitialStepPreSplitting_cff')
    process.InitialStepPreSplittingTask.remove(process.initialStepTrackRefsForJetsPreSplitting)
    process.InitialStepPreSplittingTask.remove(process.caloTowerForTrkPreSplitting)
    process.InitialStepPreSplittingTask.remove(process.ak4CaloJetsForTrkPreSplitting)
    process.InitialStepPreSplittingTask.remove(process.jetsForCoreTrackingPreSplitting)
    process.InitialStepPreSplittingTask.remove(process.siPixelClusters)
    process.InitialStepPreSplittingTask.remove(process.siPixelRecHits)
    process.InitialStepPreSplittingTask.remove(process.MeasurementTrackerEvent)
    process.InitialStepPreSplittingTask.remove(process.siPixelClusterShapeCache)

    # Redefinition of siPixelClusters: has to be after RecoTracker.IterativeTracking.InitialStepPreSplitting_cff 
    process.load("RecoLocalTracker.SiPixelClusterizer.SiPixelClusterizer_cfi")

    from RecoTracker.TkSeedingLayers.PixelLayerTriplets_cfi import *
    process.PixelLayerTriplets.BPix.HitProducer = cms.string('siPixelRecHitsPreSplitting')
    process.PixelLayerTriplets.FPix.HitProducer = cms.string('siPixelRecHitsPreSplitting')
    from RecoPixelVertexing.PixelTrackFitting.PixelTracks_cff import *
    process.pixelTracksHitTriplets.SeedComparitorPSet.clusterShapeCacheSrc = 'siPixelClusterShapeCachePreSplitting'
    process.RecoForDQM_TrkReco = cms.Sequence(process.offlineBeamSpot*process.MeasurementTrackerEventPreSplitting*process.siPixelClusterShapeCachePreSplitting*process.recopixelvertexing*process.InitialStepPreSplitting)

    if (process.runType.getRunType() == process.runType.hi_run):
        process.SiPixelClusterSource.src = cms.InputTag("siPixelClustersPreSplitting")
        process.Reco = cms.Sequence(process.siPixelDigis*process.pixeltrackerlocalreco)

    else:
        process.Reco = cms.Sequence(process.siPixelDigis*process.siStripDigis
                                    #*process.siStripZeroSuppression
                                    *process.trackerlocalreco)
                                    #*process.siStripClusters*process.siPixelClusters)


    process.p = cms.Path(
      process.hltHighLevel #trigger selection
     *process.scalersRawToDigi
     *process.Reco
     *process.siPixelClusters
     *process.DQMmodules
     *process.RecoForDQM_TrkReco
     *process.siPixelPhase1OnlineDQM_source_pprun
     *process.siPixelPhase1OnlineDQM_harvesting
    )
    
### process customizations included here
from DQM.Integration.config.online_customizations_cfi import *
process = customise(process)

#--------------------------------------------------
# Heavy Ion Specific Fed Raw Data Collection Label
#--------------------------------------------------

print "Running with run type = ", process.runType.getRunType()
