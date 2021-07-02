function [cv,cvdata]=singleDbsSubtract(obj,index,volt)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu         1/11/2017
% same code as dbsSubtract.m, but modified for single background
% subtraction, where the Nth=index background is selected for subtraction.
%
% outlier detection becomes more complicated. strategy used in
% dbsSubtract.m does not work here. Im going to remove outliers detected in
% dbsSubtract.m from the dataset produced with this and the other function
% before doing comparisons.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
data=flip(obj.FSCV,1);
time=obj.time;
ssize=9; %sample size for averaging
tmp=obj.extractFSCVtrace(volt);
tmp2=obj.extractStimulationIndices;
tot=length(tmp2);
cv=zeros(size(obj.FSCV,1),tot);
cvdata=zeros(2,tot); %2nd row for other stuff
bindex=tmp2(index); %time index of Nth background
background=mean(data(:,bindex-ssize:bindex),2);
for i=1:tot-1
    [~,findex]=max(tmp(tmp2(i):tmp2(i+1)));
    findex=findex+tmp2(i)-1;
    indices=findex-floor(ssize/2):findex+floor(ssize/2); %centered averaging
    foreground=mean(data(:,indices),2);
    cv(:,i)=foreground-background;
    cvdata(1,i)=mean(time(indices));
    cvdata(2,i)=time(findex)-time(bindex); %delay stimulation-max current
end
[~,findex]=max(tmp(tmp2(tot):end));
findex=findex+tmp2(tot)-1;
foreground=mean(data(:,findex-floor(ssize/2):findex+floor(ssize/2)),2);
cv(:,tot)=foreground-background;
cvdata(1,tot)=mean(time(findex-floor(ssize/2):findex+floor(ssize/2)));
cvdata(2,tot)=time(findex)-time(bindex);
end

