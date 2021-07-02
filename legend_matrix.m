function [str]=legend_matrix(cvdata)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        10/25/2016
% the argument is a voltammogram data matrix (returned for instance by 
% function dbsSubtract.m) and it returns a text cell array containing the
% times for each voltammogram corresponding to the argument.
% example of usage:
%  plot(cv(:,:));
%  legend(str);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
str={};%cell array to contain legend strings for the plot
tot=size(cvdata,2);
for i=1:tot
   str{i}=[num2str(cvdata(1,i)/60,'%.3g') ' m'];%3 digit precision 
end