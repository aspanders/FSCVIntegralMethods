function [cvM,av,var]=artifactRemoval(cvc,varargin)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu         2/07/2017
% The argument is a background subtracted voltammogram matrix. If good  
% voltammogram template and variability vectors are know, they can be 
% passed as optional arguments (they can be computed using a subset of 
% voltammograms where artifacts are not prominent). 
% The function returns a modified BSV matrix, with spike-type artifacts 
% reduced (or removed if good template/variability are available) 
% from each voltammogram. 
% 
% The function uses a similar idea to that described in Robinson et al.,  
% Clinical Chemistry 49 (2003) 1763
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
numvarargs = length(varargin);
if numvarargs > 2
    % throw error if there is more than 2 optional input
    error('myfuns:extractFSCVtrace:TooManyInputs', ...
        'requires at most 2 optional inputs');
elseif numvarargs == 1
    error('myfuns:extractFSCVtrace:TooManyInputs', ...
        'requires 2 optional inputs');
elseif numvarargs ==2
    av = varargin{1};
    var = varargin{2};
else
    av=mean(cvc,2); % template from hopefully relatively clean data
    var=std(cvc');var=var';
end
cvM=cvc;
[apeak,apeakloc]=max(av(:),[],1);
threshold=0.9; %decreasing this value doesn't improve results significantly
for j=1:size(cvc,2)
    scale=cvc(apeakloc,j)/apeak;
    above=find(cvc(:,j)>scale*(av+threshold*var));
    below=find(cvc(:,j)<scale*(av-threshold*var));
    cvM(above,j)=scale*(av(above)+threshold*var(above));
    cvM(below,j)=scale*(av(below)-threshold*var(below));
end