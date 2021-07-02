function [peaks,smooth,smoothp,smoothpp,smoothppp]=differential_analysis(cv,sensingVoltage)
[~,switching]=max(sensingVoltage); %%% sensingVoltage param can be replaced
N=size(cv,2);                      %%% by a switching potential parameter 
charge=zeros(4,N);
%% smoothing the data %%%%%%%%%
smooth=0.*cv;
x=1:size(cv,1);
eps=1e-4; %smoothness parameter. 1e-3 works fine, but check if data too noisy
for i=1:N
    smooth(:,i)=csaps(x,cv(:,i),eps,x);
end
%% critical and inflection points %%%%%%%%%
%computing pseudo-derivatives
smoothp=0.5*(smooth(3:end,:)-smooth(1:end-2,:));
smoothpp=smooth(3:end,:)-2*smooth(2:end-1,:)+smooth(1:end-2,:);
smoothppp=0.5*(smooth(5:end,:)-2*smooth(4:end-1,:)+...
    2*smooth(2:end-3,:)-smooth(1:end-4,:));
%% find peaks during anodic sweep
peaks=zeros(1,N);
for i=1:N
    tmp=find(smoothp(1:switching-1,i).*smoothp(2:switching,i)<=0);
    tmp=tmp(smoothpp(tmp,i)<0); %select maxima
    tmp=tmp(cv(tmp,i)>0);       %assume positive current at maxima
    tmplen=length(tmp);
    peaklen=size(peaks,1);
    if(tmplen>peaklen)
        peaks=[peaks;zeros(tmplen-peaklen,N)];
    end
    peaks(1:tmplen,i)=tmp;
end
