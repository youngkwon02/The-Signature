import cv2
import os

def putLogo(email, imgPath,str_number):
    image = cv2.imread(imgPath)
    overlay = image.copy()
    x = int(image.shape[1] / 11)
    y = int(image.shape[0] / 9) * 5
    imageWithLogo = cv2.putText(overlay, "The Signature", (x, y), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, fontScale=1.1,
                                thickness=2, color=(179, 174, 174))

    alpha = 0.8  # Transparency factor.
    image_logo = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    logoImgDir = './signMaker/static/logo_result/' + email + '/'
    if os.path.isdir(logoImgDir)==False:
        os.mkdir(logoImgDir)

    cv2.imwrite(logoImgDir + 'handwriting_name' + str(str_number) + '.png', image_logo)
