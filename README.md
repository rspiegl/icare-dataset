# Innsbruck CNN Abstract Rule Eyetracking (ICARE) Dataset
Raw data can be downloaded on https://iis.uibk.ac.at/datasets/icare <br>
Scripts to interpret collected data from the study on a comparison between humans and CNNs with eye tracking data.
Only images that participants saw are included in the data.

### Datasets
**PSVRT** from <br>
Ricci, M., Kim, J., & Serre, T. (2018). [Same-different problems strain convolutional neural networks.](https://arxiv.org/abs/1802.03390) arXiv preprint arXiv:1802.03390.

**SVRT** from <br>
Fleuret, F., Li, T., Dubout, C., Wampler, E. K., Yantis, S., & Geman, D. (2011). [Comparing machines and humans on a visual categorization test.](https://www.pnas.org/content/108/43/17621) Proceedings of the National Academy of Sciences, 108(43), 17621-17625.

**Checkerboard** from <br>
Stabinger, S., & Rodriguez-Sanchez, A. (2017). [Evaluation of deep learning on an abstract image classification dataset.](https://arxiv.org/abs/1708.07770) In Proceedings of the IEEE International Conference on Computer Vision Workshops (pp. 2767-2772).

Task list:
* PSVRT
  * sr
  * sd
* SVRT
  * svrt1
  * svrt19
  * svrt20
  * svrt21
* Checkerboard
  * Fixed camera position 5 and 1 pawn(s) (fp5 & fp1)
  * Random board placement 5 and 1 pawn(s) (rbp5 & rbp1)
  * Camera rotation 5 and 1 pawn(s) (cr5 & cr1)

PyGazeAnalyser was modified under the GPLv3 license and the changes were uploaded to https://github.com/rspiegl/PyGazeAnalyser.