background1 = spectrum_mha_to_csv('Background_20150729_082625.mha','background_1.csv');
background2 = spectrum_mha_to_csv('Background_20150729_082801.mha','background_2.csv');
background3 = spectrum_mha_to_csv('Background_20150729_082844.mha','background_3.csv');
background4 = spectrum_mha_to_csv('Background_20150729_082943.mha','background_4.csv');
gel1 = spectrum_mha_to_csv('Gel_20150729_083234.mha','gel_1.csv');
gel2 = spectrum_mha_to_csv('Gel_20150729_083419.mha','gel_2.csv');
tumor1 = spectrum_mha_to_csv('Tumor_20150729_083839.mha','tumor_1.csv');
tumor2 = spectrum_mha_to_csv('Tumor_20150729_083849.mha','tumor_2.csv');
tumor3 = spectrum_mha_to_csv('Tumor_20150729_083900.mha','tumor_3.csv');
tumor4 = spectrum_mha_to_csv('Tumor_20150729_083906.mha','tumor_4.csv');
tumor5 = spectrum_mha_to_csv('Tumor_20150729_083942.mha','tumor_5.csv');
tumor6 = spectrum_mha_to_csv('Tumor_20150729_084028.mha','tumor_6.csv');


% concatentate all the data
% skip first row in each, since those are wavelengths in nm
% add a label for the type of data
spectrumValues = background1(1,:);
allDataBackgroundVsGel = [...
           background1(2:end,:) zeros(size(background1,1)-1,1);...
           background2(2:end,:) zeros(size(background2,1)-1,1);...
           background3(2:end,:) zeros(size(background3,1)-1,1);...
           background4(2:end,:) zeros(size(background4,1)-1,1);...
           gel1(2:end,:) zeros(size(gel1,1)-1,1);...
           gel2(2:end,:) zeros(size(gel2,1)-1,1);...
           tumor1(2:end,:) ones(size(tumor1,1)-1,1);...
           tumor2(2:end,:) ones(size(tumor2,1)-1,1);...
           tumor3(2:end,:) ones(size(tumor3,1)-1,1);...
           tumor4(2:end,:) ones(size(tumor4,1)-1,1);...
           tumor5(2:end,:) ones(size(tumor5,1)-1,1);...
           tumor6(2:end,:) ones(size(tumor6,1)-1,1)...
           ];
            
%beginWavelengthIndex = 1650; % corresponds to 550.0197 nm
%endWavelengthIndex = 2513; % corresponds to 749.9252 nm
% 744 350.053827892384
% 860 375.008099295752
% 975 399.944963524382
% 1090 425.073712381687
% 1203 449.947543225874
% 1316 474.997146030233
% 1428 499.993885935232
% 1539 524.928739673887
% 1650 550.019694645496
% 1760 575.034215321219
% 1869 599.963957324334
% 1978 625.031436961700
% 2086 650.000634127649
% 2194 675.096797083186
% 2301 700.081756331100
% 2407 724.948190316797
% 2513 749.925166339385
% 2619 775.008799430466
% 2724 799.957128869329
% 2829 825.002524408259
% 2933 849.901365752816
% 3037 874.888059467757
Indices = [744 860 975 1090 1203 1316 1428 1539 1650 1760 1869 1978 2086 2194 2301 2407 2513 2619 2724 2829 2933 3037]';
%Indices = [1650 1869]';
measurements = allDataBackgroundVsGel(:,Indices);
group = allDataBackgroundVsGel(:,3649);
figure;
svmStruct = svmtrain(measurements,group,'kernel_function','linear','autoscale','true');

useMATLABClassifier = 0;
resultgroup = [];
if (useMATLABClassifier == 1)
    resultgroup = svmclassify(svmStruct,allDataBackgroundVsGel(:,Indices));
else
    resultgroup = svmclassifylinear(svmStruct,allDataBackgroundVsGel,Indices);
end

generateConfusionMatrix(resultgroup,group);

% Andras: These are what you are interested in!
Indices;
Weights = svmStruct.SupportVectors' * svmStruct.Alpha;
Bias = svmStruct.Bias;

% correction may be necessary
if (~isempty(svmStruct.ScaleData))
    ScaleShifts = svmStruct.ScaleData.shift;
    ScaleFactors = svmStruct.ScaleData.scaleFactor;
    sumScaledShifts = 0;
    for j=1:1:size(Indices,1)
        sumScaledShifts = sumScaledShifts + (Weights(j) * ScaleShifts(j) * ScaleFactors(j));
        Weights(j) = Weights(j) * ScaleFactors(j);
    end
    Bias = Bias + sumScaledShifts;
end