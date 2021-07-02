function [peaks,backs]=subtractionIndices(trace,cursor)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu         1/27/2017
% the arguments are a voltage trace vector, and a cursor object, containing
% the TIME INDEX  indicating when the background current stabilization
% period ended. The function returns a couple of vectors containg the TIME
% INDICES of the current peaks, and of the backround currents before each
% peak. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
x=1:length(trace);
strace=csaps(x,trace,1e-2,x);
stracep=0.5*(strace(3:end)-strace(1:end-2));
startI=cursor.Position(1);%search start index (after current stabilization)
ave=mean(stracep(startI:end));
variation=std(stracep(startI:end));
outliers=find(abs(stracep(startI:end)-ave)> variation);%find portions of rapid signal variation
outliers=outliers+startI-1; %shift by search start index
signsw=find(stracep(outliers(1:end-1)).*stracep(outliers(2:end))<0);%location of derivative sign changes
i=1;
j=1;
k=1;
while k<length(signsw)
    b(i)=outliers(j);
    range=outliers(signsw(k)):outliers(signsw(k)+1);
    range=range+1;%index shift because of centered derivatives
    [~,tmp]=max(trace(range));
    p(i)=range(tmp);
    j=signsw(k+1)+1;
    k=k+2; %skipping end of peak response in trace
    i=i+1;
end
j=signsw(end-1)+1;
b(i)=outliers(j);
range=outliers(signsw(end)):outliers(signsw(end)+1);
range=range+1;%index shift because of centered derivatives
[~,tmp]=max(trace(range));
p(i)=range(tmp);
peaks=p;
backs=b;