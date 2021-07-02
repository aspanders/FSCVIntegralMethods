function [boundary]=limitsWithCond(data,info,center,switching)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        9/04/2016
% Arguments are a data matrix, a corresponding info matrix, a row vector 
% containing the centers for each column (matrix and info must have same 
% size) and a hard limit for the right limit (e.g. switching potential). 
% The values in info are used to evaluate a CONDITION which 
% the zeros of each column have to SATISFY.
% Then, the function finds the closest zeros that surround the center            
% (and satisfy the cond) and returns these zeros in a 2-row matrix
% In order to work correctly, the algorithm assumes that the values in 
% the center vector ARE NOT in the corresponding columns of data. Otherwise
% the boundaries selected are going to include the points in center.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
N=size(data,2); %number of columns
boundary=zeros(2,N);
for i=1:N
    tmp=find(data(1:end-1,i).*data(2:end,i)<=0); %finding zeros
    tmp2=find(info(tmp,i)>0);%zeros whose info values are >0
    tmp=tmp(tmp2);           %select subset SATISFYING THE CONDITION
    [w wI]=min(abs(center(i)-tmp));%the rest is the same as select_limits.m
    boundary(1,i)=tmp(wI);       
    if(center(i)-boundary(1,i))>0    
        tmp2=tmp(find(center(i)< tmp));
    else
        tmp2=tmp(find(center(i)>tmp));
    end
    [w wI]=min(abs(center(i)-tmp2));   
    boundary(2,i)=tmp2(wI);       
end
boundary=sort(boundary,1);
test=boundary(2,:)>switching; 
boundary(2,test)=switching;  
end

