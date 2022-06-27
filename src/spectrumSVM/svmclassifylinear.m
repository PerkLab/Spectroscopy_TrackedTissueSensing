function resultgroup = svmclassifylinear(svmStruct,data,Indices)

    % These are important for the classification
    Weights = svmStruct.SupportVectors' * svmStruct.Alpha;
    Bias = svmStruct.Bias;
    
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
    
    % Output variable
    resultgroup = zeros(size(data,1),1);
    sumWeightedValuesArray = zeros(size(data,1),1);
    
    % actual classification
    for i=1:1:size(data,1)
        sumWeightedValues = Bias;
        for j=1:1:size(Indices,1)
            spectrumIndex = Indices(j);
            sumWeightedValues = sumWeightedValues + (Weights(j) * data(i,spectrumIndex));
        end
        sumWeightedValuesArray(i) = sumWeightedValues;
        if sumWeightedValues < 0
            resultgroup(i) = 1;
        else
            resultgroup(i) = 0;
        end
    end
    
end
