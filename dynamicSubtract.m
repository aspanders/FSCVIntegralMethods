function [voltammogram, vtime]=dynamicSubtract(obj,cursor_A,cursor_B,varargin)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        8/15/2016
%
% the arguments are a WincsWare object (defined with Jame's WincsWare 
% class), and a couple of cursor structures which contain the time
% coordinates of the voltammogram to be analyzed and its corresponding 
% background current.
% the function returns the background subtracted - and averaged - 
% voltammogram, and its corresponding time. Calculation of the background 
% and foreground are done by averaging ssize voltammograms.
%
% NOTE: time coordinates could be either time or time indices. By default
% the code assues times, but if indices are passed, the optional argument
% should be a non-empty string.
% 
% NOTE: if there is an `Index exceeds matrix dimensions' error, that
% probably means that the cursors passed to the function contain time index
% information instead of time information, but this was not communicated to
% the function. 
% When the cursors contain time information (not time indices), the
% function assumes that the measurement was taken at 10 Hz, which is 
% why the time indices are calculated by a power of 10 shift.   
%   
% modified:     1/27/2017   added an optional parameter to select between
%                           time and time index arguments for the cursors
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
numvarargs = length(varargin);
if numvarargs > 1
    % throw error if there is more than 2 optional input
    error('myfuns:extractFSCVtrace:TooManyInputs', ...
        'requires at most 1 optional input');
elseif numvarargs == 1
    type = varargin{1};
    if strcmp(type,'time')
        display('assuming cursor passed indicates a time...');
    else
        display('assuming cursor passed indicates a time index...');
    end
else
    type = 'time';
    display('assuming cursor passed indicates a time...');
end
data=flip(obj.FSCV,1);
time=obj.time;
ssize=10; %sample size for averaging
if strcmp(type,'time')
    bindex=int32(cursor_A.Position(1)*10);%time index of background current
    findex=int32(cursor_B.Position(1)*10);%time index of data point
else
    bindex=cursor_A.Position(1);%time index of background current
    findex=cursor_B.Position(1);%time index of data point
end
indices=findex-floor(ssize/2):findex+floor(ssize/2); %centered averaging
background=mean(data(:,bindex-ssize:bindex),2);
foreground=mean(data(:,indices),2);
voltammogram=foreground-background;
vtime=mean(time(indices));
disp(['Foreground time index is ' num2str(findex) char(10) 'Background time index is ' num2str(bindex)]);
end