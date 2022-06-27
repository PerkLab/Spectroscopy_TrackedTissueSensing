function generateConfusionMatrix(predictions, groundTruths)

    FalseNegatives = 0;
    FalsePositives = 0;
    TrueNegatives = 0;
    TruePositives = 0;
    
    for i=1:size(predictions,1)
        if (predictions(i)==groundTruths(i))
            if (predictions(i) == 0)
                TrueNegatives = TrueNegatives + 1;
            else
                TruePositives = TruePositives + 1;
            end
        else
            if (predictions(i) == 0)
                FalseNegatives = FalseNegatives + 1;
            else
                FalsePositives = FalsePositives + 1;
            end
        end
    end
    
    fprintf('CONFUSION MATRIX:\n')
    fprintf('        TrueNeg TruePos\n');
    fprintf('PredNeg %d %d\n',TrueNegatives,FalseNegatives);
    fprintf('PredPos %d %d\n',FalsePositives,TruePositives);
    
end
