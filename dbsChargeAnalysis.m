function [charge,bdryPairs]=dbsChargeAnalysis(cv,cvdata,sensingVoltage,varargin)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Author: Leonardo Espin          espin.leonardo@mayo.edu        01/26/2017
% the arguments are a voltammogram matrix, and voltammogram data matrix,
% the sensing voltage function used for obtaining the voltammograms, and 
% two optional parameters that indicate (a) a text label containing
% date and name information about the DBS recording, to be included in 
% plots, and (b) a row vector containing the centers around which the 
% integration boundaries are going to be computed.
% 
% The function returns a charge matrix with 3 rows: The first one for true
% charges, the second one for inflection charges and third one for
% curvature charges (using the naming conventions of the charge calculation
% manuscript). The function also returns a matrix containing 3 boundary
% pairs: true, inflection and curvature boundaries.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
numvarargs = length(varargin);
[~,switching]=max(sensingVoltage);
if numvarargs > 2
    % throw error if there is more than 2 optional input
    error('myfuns:extractFSCVtrace:TooManyInputs', ...
        'requires at most 2 optional inputs');
elseif numvarargs == 1
    date_label = varargin{1};
    [~,centers]=max(cv(20:switching-20,:),[],1);
    centers=centers+19;
    display('using peak currents during anodic sweep as centers...');
elseif numvarargs ==2
    date_label = varargin{1};
    centers = varargin{2};
else
    date_label = [];
    [~,centers]=max(cv(20:switching-20,:),[],1);
    centers=centers+19;
    display('using peak currents during anodic sweep as centers...');
end
%%  "true" limits of integration %%%%%%%%%
injections=size(cv,2);
charge=zeros(3,injections);
bdry=zeros(2,injections);
bdry=select_limits(cv,centers,switching); 
%% inflection points as limits of integration  %%%%%%%%%
[~,~,~,smoothpp,smoothppp]=differential_analysis(cv,sensingVoltage);
bdry2=select_limits(smoothpp,centers,...
    switching-1)+1;%shifts because of centered differences
%%  max curvature around peak as limits of integration  %%%%%%%%%
bdry3=limitsWithCond(smoothppp,smoothpp(2:end-1,:),...
    centers,switching-2)+2;%shifts because of centered differences
%%% --------- code below optional --------%%%
%%% if just trying to test how reasonable the limits found in bdry3 are %%
test=bdry3(1,:)<bdry(1,:); %check if left limit produces negative areas
bdry3(1,test)=bdry(1,test); 
test=bdry3(2,:)>bdry(2,:); %check if right limit produces negative areas
bdry3(2,test)=bdry(2,test); 
bdry3=sort(bdry3,1); %making sure boundaries are in ascending order
%%%  -------- code above optional --------%%%
for i=1:injections
    charge(1,i)=0.01*trapz(cv(bdry(1,i):bdry(2,i),i));
    charge(2,i)=0.01*trapz(cv(bdry2(1,i):bdry2(2,i),i));
    charge(3,i)=0.01*trapz(cv(bdry3(1,i):bdry3(2,i),i));
end
bdryPairs=[bdry;bdry2;bdry3];
%% plotting results below
%% inspecting the results %%%%%%%%%%%%
figure
hold on
plot(cvdata(1,:)/60,sensingVoltage(centers),'y*')
plot(cvdata(1,:)/60,sensingVoltage(bdry(1,:)),'r+')
plot(cvdata(1,:)/60,sensingVoltage(bdry3(1,:)),'kx')
plot(cvdata(1,:)/60,sensingVoltage(bdry(2,:)),'r+')
plot(cvdata(1,:)/60,sensingVoltage(bdry3(2,:)),'kx')
legend('peak','true','curvature','true','curvature','Location','northwest')
xlabel('Stim. time (m)')
ylabel('Voltage (V)')
title(['Ox. peaks + int. bdries' date_label])

figure
plot(cvdata(6,:),charge(3,:),'+');
title(['Total ox. charge (curvature bdries)' date_label])
xlabel('Duty cycle (%)')
ylabel('Charge (pC)')

figure;hold on
plot(cvdata(4,:),charge(3,:),'k.')
%plot(cvdata(4,:),charge(2,:),'gx')
title(['Total ox. charge ' date_label])
%legend('curvature','inflection','Location','northwest')
legend('curvature','Location','northwest')
xlabel('Stim. amplitude (mA)')
ylabel('Charge (pC)')
