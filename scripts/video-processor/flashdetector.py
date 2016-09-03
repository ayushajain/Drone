import cv2
from flashroi import FlashROI


class FlashDetector(object):
    """ FlashDetector class for detecting flash patterns

    Attributes:
        searching_pattern (str): contains a string with 1s and 0s of the binary pattern we are searching for
        frame_count (int): number of frames processed. Used to make sure that rois close to another flash object don't
            overlap
        flash_rois (list of FlashROI): contains each of the possible flashes determined from the video capture
        last_frame (numpy.ndarray): the last frame processed, for cv2.absdiff()
        params (dict): parameters for processing with:
            'blur': amount of blurring
            'threshold': threshold for binary threshold
            'scale': scaling size for each frame

    """

    def __init__(self, pattern, params):
        """ FlashDetector constructor

        We initialize the frame count in order to count the frames so that when self.validate_rois() is called, the rois
        don't overlap into the same FlashROI object. We also save the previous processed frame to last_frame for
        calculating the absolute difference in self.filters()

        Args:
            pattern (str): contains a string with 1s and 0s of the binary pattern we are searching for
            params (dict): parameters for processing with:
                'blur' (int): amount of blurring
                'threshold' (int): threshold for binary threshold
                'scale' (float): scaling size for each frame

        """

        self.searching_pattern = pattern
        self.params = params
        self.frame_count = 0
        self.flash_rois = []
        self.last_frame = None

    def filter(self, image, image_comparison, inverse=False):
        """ Performs high pass and low pass filters to eliminate noise

        First we grayscale the image since we dont want to deal with other channels (we only want light intensity).
        Then we blur the image based on the drone's altitude. We then find the absolute difference between the current
        filtered frame and the previous filtered frame, which should show brighter and larger dots where some roi
        flashed. We then threshold the frame in order to eliminate all the darker spots, and so that we can find all the
        contours. (cv2.findContours() requires that the frame be thresholded)

        Args:
            image (numpy.ndarray): frame to be filtered [3 channels]
            image_comparison (numpy.ndarray): previous filtered used to calculate absolute difference [2 channels]
            inverse (bool): thresholds first then performs abs difference if true

        Returns:
            tuple: returns `absolute difference frame` and `grayscaled frame` respectively

        """

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mask = cv2.GaussianBlur(gray, (int(self.params["blur"]), int(self.params["blur"])), 0) # TODO: blur based on altitude
        self.last_frame = mask

        if inverse:
            (t, mask) = cv2.threshold(mask, float(self.params["threshold"]), 255, cv2.THRESH_BINARY)
            mask = cv2.absdiff(mask, mask if image_comparison is None or image_comparison.shape != mask.shape else image_comparison)
        else:
            mask = cv2.absdiff(mask, mask if image_comparison is None  or image_comparison.shape != mask.shape else image_comparison)
            (t, mask) = cv2.threshold(mask, float(self.params["threshold"]), 255, cv2.THRESH_BINARY)

        return mask, gray

    @staticmethod
    def identify_contours(filtered, image_intensity, offset=(0, 0)):
        """ Finds all the contours in a thresholded frame

        This method will find all the contours in a thresholded frame. It will also calculate each of the contours
        moments, giving us more information about their features. Using each of the moments, we can then calculate the
        center of each contour, and save the image intensity at the center for each contour.

        Args:
            filtered (numpy.ndarray): fully filtered frame [2 channels]
            image_intensity (numpy.ndarray): grayscaled frame [2 channels]

        Returns:
            list of dicts: each dict contains information about the blob with:
                'location' (tuple): containing the `x` and `y` coordinates respectively
                'value' (int): color intensity of the blob

        """

        contours = []

        # Find contours on filtered frame
        blobs = cv2.findContours(filtered.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in blobs[0]:
            # Calculate moments and other features about the contours
            moments = cv2.moments(c)

            try:
                # calculate center of contour
                center_x = int((moments["m10"] / moments["m00"]))
                center_y = int((moments["m01"] / moments["m00"]))
                contours.append({"location": (center_x + offset[0], center_y + offset[1]), "value": image_intensity[center_y + offset[1]][center_x + offset[0]]})

            except ZeroDivisionError:
                pass

        return contours

    def validate_rois(self, regions_of_interest):
        """ Determines whether a contour is a region of interest

        We iterate through each region of interest, and compare each roi to all of the FlashROIS we already determined.
        If the roi's meanshift distance to the FlashROI is fairly small then we can assume that the roi is the same as
        the FlashROI. We then push the roi's image intensity value to the corresponding FlashROIs. If a roi does not
        correspond to an existing FlashROI, we create a new FlashROI object for it.

        Args:
            regions_of_interest: the contours found in the last frame processed

        Returns:
            None

        """
        for roi in regions_of_interest:
            flash_exists = False

            for fr in self.flash_rois:

                # mean-shift calculation here
                if fr.distance_to(roi['location']) < 50: # TODO: change distance to pixel based on drone altitude and implement object tracking
                    flash_exists = True

                    # push bit to flash and update location
                    if fr.last_update != self.frame_count:
                        fr.last_update = self.frame_count
                        fr.push_raw_bits(roi['value'], 80, 1)  # TODO: dynamically change pixel intensity value based on ambience
                        fr.update_location(roi['location'])

            # define a flash object if one does not already exist
            if not flash_exists:
                self.flash_rois.append(FlashROI(roi['location']))

    def identify_flash(self, image, debug=False):
        """ Finds the coordinates of the flash with the correct pattern

        In order to find the flash, first we filter out the noise. Then we identify all the contours in the resulting
        frame. We then validate each of the rois and push their intensity values to its corresponding FlashROI. After
        that, we iterate through each of the FlashROIs to check if any of them have the correct pattern.

        Args:
            image (numpy.ndarray): the frame in which we need to identify the flash
            debug (boolean): debugging

        Returns:
            FlashROI: returns the `FlashROI` if found or `None` if nothing is found

        """

        filtered, gray = self.filter(image, self.last_frame)
        contours = FlashDetector.identify_contours(filtered, gray)
        self.validate_rois(contours)

        # draw contours identified in image
        for contour in contours:
            cv2.circle(image, contour["location"], 1, (0, 0, 255), -1)

        self.frame_count += 1

        # identify correct flash
        flash_identified = None

        for flash in self.flash_rois:
            if debug:
                print flash
            # draw each flashes identifying number
            cv2.putText(image, str(flash.identity), (flash.x, flash.y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            if flash.equals_pattern(self.searching_pattern, 5):
                flash_identified = flash

        return flash_identified, image

    def correct(self, val):
        for flash in self.flash_rois:
            if flash.identity == val:
                return flash

    def track(self, flash, image, size=30):
        """ tracks the flash in the image

        Args:
            flash (FlashROI): the flash we identified
            image (numpy.ndarray): image that needs to be proccessed
            size (int): size of the box where we search for the flash

        Returns:
            FlashROI: returns the `FlashROI` if found or `None` if nothing is found

        """

        # TODO: verify the pattern as we track it

        filtered, gray = self.filter(image, self.last_frame)
        offset = max(0, flash.x - size), max(0, flash.y - size)

        # crop matrix to perform fewer contour calculations
        filtered = filtered[max(0, flash.y - size):max(0, flash.y + size), max(0, flash.x - size): max(0, flash.x + size)]

        contours = FlashDetector.identify_contours(filtered, gray, offset)
        self.validate_rois(contours)

        # draw contours identified in image and draw box around the area we are tracking
        for contour in contours:
            cv2.circle(image, contour["location"], 1, (0, 0, 255), -1)
        cv2.rectangle(image, (offset), (offset[0] + size*2, offset[1] + size*2), (250, 100, 100), 1)

        self.frame_count += 1

        return None if len(self.flash_rois) < 1 else self.flash_rois[0], image
