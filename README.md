#  Property Classification

Assessing the current status of a property is a major building block for any market value analysis. Ideally one would have to send a property-inspector to analyse a property in a timely basis. With growing properties in the United States this task becomes tedious and expensive. Ideally, only 5-10% of all the property may need an on-site inspection, rest 90% of the properties simply add up to the expense. In this project we aim to programatcally find these 5-10% of the properties that may need invidual inspection. Doing so we cut inspection cost by 70-80%. 

While there are many advance usecases that needs to be met for a complete inspection profiling, in this project we aim to cover the most basic use case. We use deep learning models to classify images of properties local to the state of Illinois into two categories suggesting if it is occupied or otherwise.

An ensemble model is built over the output probabilities of three neural networks trained over three types of images of the properties, namely the aerial view, streetside view and an overlaid (combinatorial aerial - OpenStreetMap) view. The overall accuracy achieved by the best model is 95% with an accuracy of 96% in identifying land properties.


## Data availability
* Assessor Image: Property images are collected manually once in 5-9 years. We are given a list of accessor image to use for the project. 

### External Data Collection and Preparation:
Inorder to increase coverage with more latest data we would need to have access to other data providers. Satellite, Aerial, streetside images from google maps and bing maps are updated every 6 month -2 years and have high coverage. A model would be more reliable in these images.

* **Satellite and Aerial images** Images collected from google maps and bing maps api.
* **Streetside** Images collected from google maps and bing maps api.
* **Building boundary coordinates** OSM provides the property parcel and building coordinates given an address. The OSM data is an open source contribution and hence the data may not be updated so frequently, albeit, changes in parcels are rare.

Here's a snapshot of the images:

<div id="image-table">
    <table>
	    <tr>
    	    <td style="padding:5px">
        	    <img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/assessor.png" width="200" height="200"><figcaption><center>Assessor Image</center></figcaption>
      	    </td>
            <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/streetside.jpg" width="200" height="200"><figcaption><center>Streetside Image</center></figcaption>
             </td>
            <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/aerial.png" width="200" height="200"><figcaption><center>Satellite/Aerial Image</center></figcaption>
             </td>
             <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/overlayed2.png" width="200" height="200"><figcaption></center>Overlaid Image</center></figcaption>
             </td>
        </tr>
    </table>
</div>
 

## Data Issues:
1. Accessor images are 5-9 years old and hence cannot be trusted entirely
2. Accessor image and labels were expensive to collect.
3. Accessor image had Poor coverage
4. Building's sometimes are occluded with trees and other property artifacts.
5. Human annotation can't be trusted entirely
6. Data Imbalance: 85.56% of data was positive class (occupied)
7. Data spatial difference. singlefamily, multifamily, condo, commercial, parking lots, office space etc.

### Problems Continued:
#### Data/Labeling problems:
1. **Incorrect Labels**: Even with the external data we see lots of our labels not consistent with the image picture. So we typically have a data issue. We plan to use all the images (Mixture of experts model). Since, there is a good chance that at least one image type would be consistent with the label. Labeling issues can not be avoided, ergo, we use a bootstrapping techniques to correct the labels and augment them per iteration. [Notebook](https://github.com/Sardhendu/PropertyClassification/blob/master/notebooks/BootStrap-Test-Mislabeled.ipynb)

2. **Data Imbalcnce**: Majority of data we had, had a property in it. We were missing on data for vacant land. With data sourcing and clever modeling techniques we were able to fix this problem.

#### Data/Modeling problems:
1. **Focus/Attention**: With multiple buildings in a image, how to tell the model to focus on the queried building? Address to lat-lon conversion results in a coordinate that could be anywhere on the property, additionally in a dense region the coordinate returned could overlap with the adjacent building structure. Since Deep learning CV models are known to perform worse on the edges of an image we may encounter several False positives/negatives. 

Paritally this problem can be solved by the use of OSM's. In sense, it could help in providing attention based context to the classification model. OSM building coordinates can be Overlaid on the image to provide additional focus point to the model. [Overlay building boundary on static images](https://github.com/Sardhendu/PropertyClassification/tree/master/src/semantic_segmentation)  Overlay building boundaries (collected from OSM) on satellite static images collected from google maps.

2. **Image Size**: How to select the size of the image generation process? Lower size image could clear up noise by reducing the number of properties in the image. But a small size image reduces context for large properties. This will affect the model performance with large properties. 

Here we bring OSM and street view images to our rescue. This problem can be ameliorated by integrating several image source.


### Data Preparation:
* “last_reviewed_timestamp” was used to initially sample x images with most likely correct labels. This process was augmentation by sample more data with Bootstrapping.
* "Balance Dataset": Dataset was balanced for training purposes and samples were taken using stratified sampling approach.
* In total training_samples 16678 = images, validation_samples = 1664 images and test_samples = 1792
* Augmentation and Cropping:
    
    1. Rotation: 90
    2. Crop(128, 128, 3) : when building polygons found then crop using that, if not then center crop using `image_crop_shape`
    3. Resize (128, 128, 3): only if the image/crop size is greater/less than the given `image_resize_shape`
    4. image_out_shape (224, 224, 3): final output shape. If zero pad then pad to size 224 if not then resize


### Modeling Techniques (Deep Nets) 
**Vanila Classification model** with input of aerial images fell short and saw several modelling problems as discussed above. Let us now discuss all different models employed for different types of images.

#### [RESNET-18](https://github.com/Sardhendu/PropertyClassification/blob/master/src/conv_net/resnet.py) + a little variation

<div id="wrapper">
    <div class="twoColumn">
         <p>
            RESNET-18 model is trained with Satellite Images from google maps. RESNET's can go very deep and are very robust to the problem of vanishing gradient. In doing so, they are able to learn very complex features within the image. The center pixel in the google extracted image is the Latitude and Longitude of the address location. We use the OSM data to crop the surronding of the building from a image. We then resize (128x128x3) and zeropad them to make a shape of 224x224x3. While 224x224x3 is not a necessity (since we dont use pretrined weights), we do it to respect the RESNET architecture. <br><br> 
         </p>
    </div>
</div>

[Notebook](https://github.com/Sardhendu/PropertyClassification/blob/master/notebooks/Model_eval-Aerial_cropped.ipynb)

<div id="image-table">
    <table>
	    <tr>
    	    <td style="padding:5px">
        	    <img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/home_cropped.jpg" width="300" height="150"><figcaption><center>House bbox cropped</center></figcaption>
      	    </td>
            <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/home_resized.png" width="200" height="200"><figcaption><center>Home Resized/Pad</center></figcaption>
             </td>
            <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/land.png" width="200" height="200"><figcaption><center>Land central crop</center></figcaption>
             </td>
        </tr>
    </table>
    <table>
        <tr>
            <td style="padding:5px">
            	<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/prec_recall_curve.png" width="600" height="200"><figcaption><center>Precision Recall Plot</center></figcaption>
            </td>
        </tr>
    </table>

</div>



--------------

#### [CONV-NET](https://github.com/Sardhendu/PropertyClassification/blob/master/src/conv_net/convnet.py)

<div id="wrapper">
    <div class="twoColumn">
        <img align="right" width="200" height="200" src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/overlayed2.png">
    </div>
    <div class="twoColumn">
         <p>
            Convnet model is trained with Overlaid Images i.e. The idea here is to expicitely provide the model with 
            the knowledge of house and land using coloring scheme. The roof top of the houses are colored red. This allows the model to 
            learn very quickly in few steps. Our experiment shows that the model was able to learn a good distinction in just 2-3 steps. We use a simple Conv-net architecture becasue now due to the colors the model no longer needs
             a deep architecture to learn simple features. We further believe that even a trandional ML model could do a descent job classifying the image. <br><br><b>Challange</b>: The 
             building boundaries required to create Overlaid images are collected from <b>Open Street map</b>. These may not 
             be updated as frequently as Google maps. Moreover, getting building boundaries for all the location may 
             not be feasible. One way to generate colored image given an satellite view is to use <b>Fully 
             Convolutional Networks for semantic segmenting</b> (TODO).<br>     
         </p>
    </div>
</div>
    
[Notebook](https://github.com/Sardhendu/PropertyClassification/blob/master/notebooks/Model_eval-Overlaid.ipynb)/[Initial Work](https://github.com/Sardhendu/PropertyClassification/tree/master/src/semantic_segmentation)

---------------

#### [CONV AUTOENCODER](https://github.com/Sardhendu/PropertyClassification/blob/master/src/conv_net/conv_autoencoder.py)

<div id="wrapper">
    <div class="twoColumn">
        <img align="right" width="200" height="200" src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/assessor2.png">
    </div>
    <div class="twoColumn">
         <p>
            Autoencoders were trained for research purposses. And they were used for Assessor/Streetside Images. Assessor images are 5-9 years old and there is a high chance that a Land property then would be a house now. This means that despite the label might say house, the image might indicate a land. So we could either trust the labels or the image. Autoencoder are unsupervised techniques that does not require a label. We feed in the autoencoder with images of house and land and leave it for the autoencoder to find an embedding that could distinguish between land and house. We create a encoding space of 64 dimensions and try k-means clustering with 2 initial centers.<br><br><b>Challange:</b> Assessor images might be expensive to obtain, since these images are manually collected by organization/individuals. In a real scenario, finding assessor image for every address is overstated.<br>    
         </p>
    </div>
</div>

[Initial Work](https://github.com/Sardhendu/PropertyClassification/blob/master/notebooks/Model-eval-AssessorEncode.ipynb)

--------


## Data Pipeline (Using Apache Airflow):

The final product submitted was an Airflow DAG that could be triggered on a need-to basis. Below is a view of Data pipeline that is achieved using Apache Airflow Framework. [Code](https://github.com/Sardhendu/PropertyClassification/blob/master/dags/train_pipeline.py)

<img src="https://github.com/Sardhendu/PropertyClassification/blob/master/images/pipeline.png" width="800" height="200"><figcaption><center>Data Pipeline</center></figcaption>

