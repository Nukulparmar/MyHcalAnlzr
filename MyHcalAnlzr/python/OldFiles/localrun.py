import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.VarParsing as VarParsing

from Configuration.StandardSequences.Eras import eras
process = cms.Process('TDC',eras.Run3)

process.load("FWCore.MessageService.MessageLogger_cfi")
process.load('Configuration.StandardSequences.Services_cff')
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32(1000)

process.load('Configuration.EventContent.EventContent_cff')
process.load("Configuration.StandardSequences.GeometryDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.RawToDigi_Data_cff")
#process.load("EventFilter.HcalRawToDigi.HcalRawToDigi_cfi")
process.load("Configuration.StandardSequences.Reconstruction_cff")
process.load("RecoLocalCalo.Configuration.hcalLocalReco_cff")
process.load('Configuration.StandardSequences.EndOfProcess_cff')
#process.load("RecoLuminosity.LumiProducer.bunchSpacingProducer_cfi")

process.load("RecoLocalTracker.SiPixelRecHits.SiPixelRecHits_cfi")

process.source = cms.Source("HcalTBSource",
	firstLuminosityBlockForEachRun = cms.untracked.VLuminosityBlockID([]),
	fileNames = cms.untracked.vstring(
		#"file:/eos/cms/store/group/dpg_hcal/comm_hcal/USC/run358080/USC_358080.root",
		'file:/eos/cms/store/group/dpg_hcal/comm_hcal/USC/run' + RUN + '/USC_' + RUN + '.root' for RUN in ['360302', '360362', '360417', '360463']
                # Set 1: ['355079', '355538', '355573', '355669', '355710']
                # Set 2: ['355776', '355838', '355882', '355947', '356016']
                # Set 3: ['356115', '356457', '356538', '356590', '356646']
                # Set 4: ['356829', '356926', '356958', '357008', '357142']
                # Set 5: ['357287', '357337', '357415', '357456', '357501']
                # Set 6: ['357564', '357622', '357646', '357743', '357787']
                # Set 7: ['357845', '357968', '357996', '358087', '358101']
                # Set 8: ['358160', '358179', '358222', '358277', '358303']
                # Set 9: ['358338', '358430', '358488', '358543', '358595']
                # Set 10:['358663', '358812', '358902', '358928', '358997']
                # Set 11:['359026', '359092', '359168', '359236', '359299']
                # Set 12:['359378', '359483', '359549', '359652', '359703']
                # Set 13:['359730', '359767', '359822', '359892', '359954']
                # Set 14:['360006', '360040', '360096', '360144', '360242']
                # Set 15:['360302', '360362', '360417', '360463']
        )
)

process.options = cms.untracked.PSet(
#	SkipEvent = cms.untracked.vstring('ProductNotFound')
)

process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.autoCond import autoCond
process.GlobalTag.globaltag = autoCond['run3_hlt']

#Setup FWK for multithreaded
process.options.numberOfThreads=cms.untracked.uint32(8)
process.options.numberOfStreams=cms.untracked.uint32(0)
process.options.numberOfConcurrentLuminosityBlocks=cms.untracked.uint32(1)


process.MyHcalAnlzr = cms.EDAnalyzer('MyHcalAnlzr',
#        tagRecHit = cms.untracked.InputTag("hbheprereco"),
#	tagQIE11 = cms.InputTag("simHcalDigis", "HBHEQIE11DigiCollection")
	tagQIE11 = cms.untracked.InputTag("hcalDigis"),
#        EEdigiCollection = cms.InputTag("ecalDigis","eeDigis"),
#	EERecHitCollection = cms.InputTag("ecalRecHit","EcalRecHitsEE")
        runtype = cms.untracked.string("Local")
)

process.TFileService = cms.Service("TFileService",
      fileName = cms.string("/eos/user/n/nparmar/HCAL/MyHcalAnlzr/output_LocalRuns_set15.root"),
      closeFileFast = cms.untracked.bool(True)
)

#process.ecalRecoSequence = cms.Sequence((process.ecalMultiFitUncalibRecHit+process.ecalDetIdToBeRecovered+process.ecalRecHit))

process.tbunpacker = cms.EDProducer(
        "HcalTBObjectUnpacker",
        IncludeUnmatchedHits    = cms.untracked.bool(False),
        HcalTriggerFED                  = cms.untracked.int32(1)
)
process.tbunpacker.fedRawDataCollectionTag = cms.InputTag("source")
process.hcalDigis.InputLabel = cms.InputTag("source")


process.p = cms.Path(
#	process.tbunpacker*
#	process.ecalDigis*
#	process.ecalRecoSequence*
        process.hcalDigis*
#	process.hcalLocalRecoSequence*
	process.MyHcalAnlzr
)

#process.outpath = cms.EndPath(process.out)
