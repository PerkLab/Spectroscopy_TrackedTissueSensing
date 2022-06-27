clc
clear all
close all

ReferenceToRAS1=[0 0 -1 0; 0 -1 0 0; -1 0 0 0 ; 0 0 0 1];
StylusTipToStylus1=[ 1 0 0 182.18; 0 1 0 0.07; 0 0 1 14.32; 0 0 0 1];
StylusModelToStylusTip1=[-1 0 0 0 ; 0 -1 0 0; 0 0 1 0; 0 0 0 1];
%ReferenceToRAS=ReferenceToRAS1(1:3,4);
%StylusTipToStylus=StylusTipToStylus1(1:3,4);
%StylusModelToStylusTip=StylusModelToStylusTip1(1:3,4);
%%script showing how to read using MhaReadTransforms

%% read data
fileToRead = 'S:/data/SlicerIGT/BreastSurgery/2015-03-06_BreachWarningLightExperimentalData/Analysis/Subject14/RecordingTumorA_20150312_174814_StylusToReference.mha';

%enter the name of the transforms as they appear in the Mha file as inputs
%to the MhaReadTransforms function
[myTransformsStructure myTransformTimestampsStructure myTransformUnfilteredTimestamps]=MhaReadTransforms(fileToRead, {'ReferenceToTracker','StylusToReference'} );
%myTransformsStructure is a struct containing both transform1 and
%transform2 data.  The timestamps structures hold the timestamps of each
%sample

%% filter data to isolate only positions
%this takes the 3x1 position vector from each transform and puts it into
%the 3xN vector transfrom1Positions
StylusTip_RAS = zeros( 3, size( myTransformsStructure.ReferenceToTrackerTransformMatrix, 3 ) );

for i = 1:size( myTransformsStructure.ReferenceToTrackerTransformMatrix, 3 )
    StylusToReference = squeeze(myTransformsStructure.StylusToReferenceTransformMatrix(:,:,i));
    StylusModelToRAS = ReferenceToRAS1*StylusToReference*StylusTipToStylus1*StylusModelToStylusTip1;
    StylusTip_RAS( :, i ) = StylusModelToRAS( 1:3, 4 ); 
    
end%for

%% example: to see the position at sample 147...
%positionAtSample147 = StylusModelToRAS(:,147); %this might need to be (147,:)
%tumors range from Y = -8.18 to Y = 12.74
%vertical bounds of tumor (ymin=-8.18, ymax=12.74)

upperBound = 8;
lowerBound = -8.18;
dataIndexesInsideBoundingRegion = ( StylusTip_RAS(2,:) > lowerBound) & ( StylusTip_RAS(2,:) < upperBound);
StylusTip_RAS_insideBoundingRegion = StylusTip_RAS(:,dataIndexesInsideBoundingRegion);

figure
scatter3(StylusTip_RAS_insideBoundingRegion(1,:),StylusTip_RAS_insideBoundingRegion(3,:),StylusTip_RAS_insideBoundingRegion(2,:));

figure;
scatter(StylusTip_RAS_insideBoundingRegion(1,:),StylusTip_RAS_insideBoundingRegion(3,:));

x=StylusTip_RAS_insideBoundingRegion(1,:);
y=StylusTip_RAS_insideBoundingRegion(3,:);
x = x - mean(x);
y = y - mean(y);

for i = 1:size(x,2)
    power = 1.005;
    lengths_sq(i) = norm([x(i) y(i)])^power;
end

x_new=x./lengths_sq;
y_new=y./lengths_sq;
k=convhull(x_new,y_new);


figure
plot(x(k),y(k),'r-',x,y,'b*')