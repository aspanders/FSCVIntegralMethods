function [boundary]=select_limits(data,center,switching)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        9/04/2016
% Arguments are a data matrix, a row vector containing the centers
% for each column (both must have equal number of columns) and a 
% hard limit for the right limit (e.g. switching potential). 
% In each column the function finds the closest zeros that surround the
% center, and returns these zeros in a 2-row matrix.
% In order to work correctly, the algorithm assumes that the values in 
% the center vector ARE NOT ZEROS in the corresponding columns of data. 
% Otherwise the boundaries selected are going to include the centers.
%   Revision:   11/28/2016  Added checks for singular cases when only 
%                           one zero around the center is found (lim check)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
N=size(data,2); %number of columns
boundary=zeros(2,N);
lim=0; % check for singular cases
for i=1:N
    tmp=find(data(1:end-1,i).*data(2:end,i)<=0); %find zeroes
    [~,wI]=min(abs(center(i)-tmp));    %zero closest to center
    boundary(1,i)=tmp(wI);             %is first boundary
    if(center(i)-boundary(1,i))>0      %1st bdry smaller than center then 
        tmp2=tmp(find(center(i)< tmp));%select zeroes larger than center
        if (isempty(tmp2))
           lim=2; %plus infinity 
        end
    else
        tmp2=tmp(find(center(i)>tmp)); %zeroes smaller than center
        if (isempty(tmp2))
            lim=1; %minus infinity
        end
    end
    if lim==0                           %if REGULAR CASE
        [~,wI]=min(abs(center(i)-tmp2));   %zero closest to ctr within selected
        boundary(2,i)=tmp2(wI);            %is second boundary
    else                                %if SINGULAR CASE
        tmp2=[1;size(data,1)];
        boundary(2,i)=tmp2(lim);
        lim=0;
    end
end
boundary=sort(boundary,1); %making sure boundaries are in ascending order         
test=boundary(2,:)>switching; %check if right limit is larger than hard limit
boundary(2,test)=switching;  
end

