function [cv,cvdata]=automaticSubtract(obj,cursor,volt)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu         1/27/2017
% the arguments are a WincsWare object (defined with Jame's WincsWare 
% class), a cursor structure which contains the TIME INDEX indicating when
% the background current stabilization period ended, and a voltage value
% for selecting a voltage trace where current spikes are going to be
% identified (for DA volt would be close to 0.6 V). 
%  
% the function returns a matrix containing (averaged) background subtracted 
% voltammograms (BSVs), and their corresponding time (first row of cvdata). 
% the function also returns the time period between the background and
% the maximum current spike (given in second row of cvdata). Calculation of 
% the background and foreground are done by averaging ssize voltammograms.
%
% NOTE: the function obtains the time indices which indicate the background
% and foreground currents by calling subtractionIndices. This indices are
% plotted on top of the voltage trace to check that the extraction of BSVs
% has been done correctly. DATA CORRECTION (and addition of BSVs that
% migh have been missed) can be done manually with the aid of the
% dynamicSubtract function. 
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
data=flip(obj.FSCV,1);
time=obj.time;
ssize=10; %sample size for averaging
trace=obj.extractFSCVtrace(volt);
[peaks,backs]=subtractionIndices(trace,cursor);
tot=length(backs);
cv=zeros(size(obj.FSCV,1),tot);
cvdata=zeros(2,tot); %2nd row for other stuff
for i=1:tot
    background=mean(data(:,backs(i)-ssize:backs(i)),2);
    indices=peaks(i)-floor(ssize/2):peaks(i)+floor(ssize/2); %centered averaging
    foreground=mean(data(:,indices),2);
    cv(:,i)=foreground-background;
    cvdata(1,i)=mean(time(indices));
    cvdata(2,i)=time(peaks(i))-time(backs(i)); %delay peak - background
end
% outlier detection:
figure
plot(trace)
hold on
plot(peaks,trace(peaks),'xr')
plot(backs,trace(backs),'xg')
%title('Outlier detection')
xlabel('time indices')
ylabel(['Current @ ' num2str(volt) 'V'])
legend('resp.','peaks','backgrounds')
msgbox({'check for correctness of data. Large artifacts can throw algorithm off';'Small current responses might be missed by data extraction algorithm';...
    'Plotting the peak-background delay (2nd row of cvdata) is a quick check for outliers.'});
end
%% example of simple outlier removal
%>eliminate=find(cvdata(2,:)>value); %value is gap in seconds
% if we manually add voltammogram indices to be eliminated
%>remove=[i j];
%>remove=[remove eliminate];
% and then we remove outliers
%>cv(:,remove)=[];cvdata(:,remove)=[]; 
%% example of manual data correction:
% first check which voltammogram is missing or incorrect, by pointing a
% cursor to the time of interest:
%
%>[tmp index]=min(abs(10*cvdata(1,:)-cursor.Position(1))) 
% mutiplication by 10 assumes that cursor contains a time index. if it has
% time information, we can compare cvdata(1,:) and the cursor directly.
% index will tell us the number of the voltammogram that we want to append
% data to, or correct, assume in this case it returns 5.
%
%>cv_new(:,1:4)=cv(:,1:4);cvdata_new(:,1:4)=cvdata(1,1:4);
%>[dv dvdata]=dynamicSubtract(obj,cur_A,cur_B,'index');
%>i=5;
%>cv_new(:,i)=dv;cvdata_new(1,i)=dvdata;
%