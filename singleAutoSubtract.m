function [cv,cvdata]=singleAutoSubtract(obj,cursor,bindex,volt)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu         1/30/2017
% based on automaticSubtract.m, it sets the background to be the Nth=bindex
% background obtained by subtractionIndices. Besides that is identical to
% automaticSubtract.m
% Outliers and erroneous BSV should be removed from both single subtracted
% data and data obtained with the automaticSubtract function. 
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
data=flip(obj.FSCV,1);
time=obj.time;
ssize=10; %sample size for averaging
[peaks,backs]=subtractionIndices(obj.extractFSCVtrace(volt),cursor);
tot=length(backs);
cv=zeros(size(obj.FSCV,1),tot);
cvdata=zeros(2,tot); %2nd row for other stuff
 background=mean(data(:,backs(bindex)-ssize:backs(bindex)),2);
for i=1:tot
    indices=peaks(i)-floor(ssize/2):peaks(i)+floor(ssize/2); %centered averaging
    foreground=mean(data(:,indices),2);
    cv(:,i)=foreground-background;
    cvdata(1,i)=mean(time(indices));
    cvdata(2,i)=time(peaks(i))-time(backs(i)); %delay peak - background
end
