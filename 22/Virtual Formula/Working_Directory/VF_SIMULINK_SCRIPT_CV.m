%% Clean Workspace 
clear all
close all
clc

%% Add Paths
addpath_vicrt_20

%% Acceleration
vicrt_inputfile = 'VI_Racer_CV_Acceleration_send_svm.xml' ;
sim('VF_Control_System_CV.slx')

%% Skidpad
vicrt_inputfile = 'VI_Racer_CV_Skidpad_send_svm.xml' ;
maxperf_inputfile = 'VI_Racer_CV_Skidpad.mxp' ;
vimaxperf_crt(maxperf_inputfile)

%% Autocross
vicrt_inputfile = 'VI_Racer_CV_Autocross_send_svm.xml' ;
maxperf_inputfile = 'VI_Racer_CV_Autocross.mxp' ;
vimaxperf_crt(maxperf_inputfile)

%% Endurance
vicrt_inputfile = 'VI_Racer_CV_Endurance_send_svm.xml' ;
maxperf_inputfile = 'VI_Racer_CV_Endurance.mxp' ;
vimaxperf_crt(maxperf_inputfile)
