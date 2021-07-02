function [cv,cvdata]=dbsSubtract(obj,volt)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        12/09/2016
% the arguments are a WincsWare object (defined with Jame's WincsWare 
% class), and a value for selecting a voltage trace where current spikes
% are going to be identified (for DA volt would be close to 0.6 V). 
%  
% the function obtains the stimulation times from the object, 
% which are used as point of selection for background currents.
% the function returns a matrix containing (averaged) background subtracted 
% voltammograms, and their corresponding time (first row of cvdata). 
% the function also returns the delay between the stimulation time and
% the maximum current spike for the stimulation, which is used for outlier
% detection (given in second row of cvdata). 
%
% stimulation artifacts that might interfere with data extraction (i.e.
% selecting an artifact peak instead of max stimulation current). when this
% happens the time delay TENDS TO BE SMALLER.
% Outliers with LARGER DELAYS tend to occur when the stimulation is too
% small and no response is produced (also stimulation misfires).
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
data=flip(obj.FSCV,1);
time=obj.time;
ssize=10; %sample size for averaging
tmp=obj.extractFSCVtrace(volt);
tmp2=obj.extractStimulationIndices;
tot=length(tmp2);
cv=zeros(size(obj.FSCV,1),tot);
cvdata=zeros(2,tot); %2nd row for other stuff
for i=1:tot-1
    bindex=tmp2(i);
    [~,findex]=max(tmp(tmp2(i):tmp2(i+1)));
    findex=findex+tmp2(i)-1;
    background=mean(data(:,bindex-ssize:bindex),2);
    indices=findex-floor(ssize/2):findex+floor(ssize/2); %centered averaging
    foreground=mean(data(:,indices),2);
    cv(:,i)=foreground-background;
    cvdata(1,i)=mean(time(indices));
    cvdata(2,i)=time(findex)-time(bindex); %delay stimulation-max current
end
bindex=tmp2(tot);
[~,findex]=max(tmp(tmp2(tot):end));
findex=findex+tmp2(tot)-1;
background=mean(data(:,bindex-ssize:bindex),2);
foreground=mean(data(:,findex-floor(ssize/2):findex+floor(ssize/2)),2);
cv(:,tot)=foreground-background;
cvdata(1,tot)=mean(time(findex-floor(ssize/2):findex+floor(ssize/2)));
cvdata(2,tot)=time(findex)-time(bindex);
% outlier detection:
figure
plot(cvdata(2,:),'x')
title('Outlier detection: stim. time - max current delay')
xlabel('Stimulation number')
ylabel('Delay (s)')
msgbox({'check for outliers.';'Stimulation artifacts can interfere with data extraction'});
end
%example of manual correction of outliers:
%check portion of trace corresponding to outlier of stimulation i:
%  obj.plotTrace(volt)
%  xlim([cvdata(1,i)-150 cvdata(1,i)+50])
%select trace cursor locations manually and use as argumens for
%dyanamicSubtract:
%  [dv dvdata]=dynamicSubtract(obj,A,B);
%replace oulier voltammogram with dv:
%  cv(:,i)=dv;
%same with time:
%  cvdata(1,i)=dvdata;
%calculate new delay using the time indices returned by dynamicSubtract
%  cvdata(2,i)=obj.time(foreground)-obj.time(background);
%check new delay by plotting on top of original outlier detection figure:
%  plot(i,cvdata(2,i),'rx')
