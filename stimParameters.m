function [data,fool]=stimParameters(obj,stimDuration,varargin)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        10/25/2016
% the arguments are a WincsWare object (defined with Jame's WincsWare 
% class), the duration of each stimulation sequence (in seconds) and 
% an optional parameter that indicates if plots for checking
% the symmetry of the electrical stimulation pulses are to be shown.
% the function returns a data matrix with 4 rows and number-of-stimulations
% columns. The first row is for the stimulation time, second for amplitude,
% third for duration, and fourth is for the duty cycle. 
% As a second -optional- output, the funtion returns an 8xn matrix
% containing the entire raw stimulation parameters, which should be used
% if stimulation pulses are not symmetric. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
numvarargs = length(varargin);
if numvarargs > 1
    % throw error if there is more than 1 optional input
    error('myfuns:extractFSCVtrace:TooManyInputs', ...
        'requires at most 1 optional input');
elseif numvarargs == 1
    % set optional parameters if they exist
    plots = varargin{1};
else
    % set required optional parameters
    plots = false;
end
stimulations=length(obj.stimulationStatus)/2;
data=zeros(8,stimulations);
for i=1:stimulations
    data(1,i)=obj.stimulationSequences.sequences{i}.pulse_amplitude;
    data(2,i)=obj.stimulationSequences.sequences{i}.pulse_amplitude_2;
    data(3,i)=obj.stimulationSequences.sequences{i}.pulse_duration;
    data(4,i)=obj.stimulationSequences.sequences{i}.pulse_duration_2;
    data(5,i)=obj.stimulationSequences.sequences{i}.pulse_interval;
    data(6,i)=obj.stimulationSequences.sequences{i}.pulse_interval_2;
    data(7,i)=obj.stimulationSequences.sequences{i}.repeat_pulse_pattern;
    data(8,i)=obj.stimulationStatus(2*i-1).time_in_seconds;
end
if plots
    figure;plot(data(1,:)+data(2,:),'x');title('if zeros, stim. amplitudes symmetric');
    figure;plot(data(3,:)-data(4,:),'x');title('if zeros, pulse duration symmetric');
    figure;plot(data(5,:),'x');title('interval between +/- stim.');
    figure;plot(data(6,:),'x');title('gap after stim.');
    figure;plot(data(7,:),'x');title('number of pulses');
    figure;plot((data(3,:)+data(4,:)).*data(7,:)*0.001/stimDuration,'x');title('Duty cycle (fraction)');
    ylabel(['stim/' num2str(stimDuration) ' s']);
    xlabel('Stimulation number')
end
fool=data;
data=zeros(4,stimulations);
data(1,:)=fool(8,:); %start of stimulation (s)
data(2,:)=fool(1,:); %stimulation amplitude (mA)
data(3,:)=fool(3,:); %duration of stimulation (ms)
data(4,:)=100*(fool(3,:)+fool(4,:)).*fool(7,:)*0.001/stimDuration;%duty cycle per stimulation (%)
end