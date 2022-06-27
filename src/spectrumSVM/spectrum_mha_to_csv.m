function imageMatrix = spectrum_mha_to_csv(input_filename,output_filename)
    % INPUT: the file name that is to be read (.mha format), add the extension
    % please

    % OUTPUT: The file name that is to be written (.csv format), add the
    % extension please. The output will be the measurements taken by the probe.
    % The first row will contain the wavelengths in nanometers

    spectrumData = mha_read_volume(input_filename,1);
    pixelData = spectrumData.pixelData;
    % pixelData(w,d,t)
    % w = wavelength index
    % d = 1 for wavelength in nm
    % d = 2 for measurement
    % t = time index

    imageMatrix = zeros(size(pixelData,3)+1,size(pixelData,1));
    % imageMatrix(t,w) with a header in top row

    for w=1:size(pixelData,1)
        imageMatrix(1,w) = pixelData(w,1,1);
    end
    for t=1:size(pixelData,3)
        imageMatrix(t+1,:) = pixelData(:,2,t);
    end
    
    csvwrite(output_filename,imageMatrix);
    
end

