# Surface segmentation

## Task
```
Image segmentation 노면 이미지에서 각 영역을 분할하는 문제
```

## Dataset
* image height = 1080, width = 1920, channel = 3

| Phase | num of image | num of mask_image | label_format |
| - | - | - | - |
| train | 32,467 | 32,467 | xml_file: 540 |
| validate |  7,028 | 7,028 | xml_file: 124 |
| test | 6,904 | 6,857 | xml_file: 136 |

## Data Directory
```
\_data
    \_ train
        \_ Surface_***
        \_ MASK, *.xml , *.jpg (images)
            \_ *.png (mask_images)
    \_ val
        \_ Surface_***
        \_ MASK, *.xml , *.jpg (images)
            \_ *.png (mask_images)
    \_ test
        \_ Surface_***
        \_ *.jpg (images)
          

image_name = "MP_SEL_SUR_033182.jpg"
mask_image_name = "MP_SEL_SUR_033182.png"
```

## Data Sample
<img width=350 src="sample_images/MP_SEL_SUR_000001.jpg"/>　　　<img width=350 src="sample_images/MP_SEL_SUR_000001.png"/>

## Data issue
<img width=700 height = 100 src="sample_images/data_error.PNG"/>

- xml Label File 내에 alley 하위 태그에 attribute가 없는 경우가 있음 \
   dataload 시 예외처리 진행하시면 됩니다. (dataload() 베이스 코드 참고) \


## class_name (21 classes)

<img width=500 src="sample_images/class_name.png"/>



## Evaluation

mAP(mask IoU = 0.5)

#Submission file(xml format)

***!!!주의 !!!!***

***prediction.xml 작성시 좌표값은 'image height = 1080, width = 1920' 기준으로 작성***

```
<predictions>
  <image name="MP_SEL_SUR_000001">
    <predict class_name="sidewalk_cement" polygon="1344,949;1344,952;1343,953;1343,959;1344,960;1345,959;1345,955;1344,954;" score="0.09568093717098236" />
    <predict class_name="alley_damaged" polygon="716,964;715,965;714,965;717,965;718,966;720,966;721,965;728,965;725,965;724,964;" score="0.06147599592804909" />
  </image>
  <image name="MP_SEL_SUR_000002">
    <predict class_name="caution_zone_tree_zone" polygon="1064,38;1062,40;1062,45;1063,46;1063,47;1066,50;1066,52;1068,54;1068,56;1071,59;1071,61;1072,62;1072,65;1073,66;1073,73;1074,74;1074,78;1075,79;1075,81;1076,82;1076,84;1078,86;1078,88;1079,88;1080,89;1081,89;1082,90;1241,90;1242,89;1245,89;1246,88;1247,88;1247,87;1248,86;1248,84;1247,83;1247,82;1245,80;1245,78;1243,76;1243,75;1242,75;1240,73;1240,72;1239,71;1239,70;1238,69;1238,68;1234,64;1233,64;1232,63;1232,62;1231,61;1231,60;1229,58;1228,58;1224,54;1224,53;1223,53;1221,51;1220,51;1219,50;1218,50;1217,49;1214,49;1213,48;1209,48;1208,47;1198,47;1197,48;1195,48;1194,49;1193,49;1192,50;1191,50;1191,51;1190,52;1190,60;1189,61;1189,62;1187,64;1184,64;1183,65;1178,65;1177,66;1170,66;1169,65;1158,65;1157,66;1148,66;1147,65;1142,65;1141,64;1138,64;1137,63;1136,63;1135,62;1133,62;1132,61;1132,60;1131,59;1131,47;1132,46;1132,45;1133,44;1133,42;1132,42;1131,41;1128,41;1127,40;1119,40;1118,39;1110,39;1109,38;" score="0.9982360601425171" />
 </image>
 ...
 ...
</predictions>

```

## Description
```
dataloader.py : img name으로 xml 파일 안에 라벨 정보를 불러온 뒤 target 이라는 딕셔너리 형태로 저장, 한 이미지 tensor와 그 이미지에 대한 label이 target이라는 딕셔너리로 매칭되는 방식

model.py : torchvision 내부에 있는 MaskRCNN model을 호출하여 사용
main.py : train, test 함수 구현, test의 경우 submission file 형식으로 저장됨.
evaluate.py : submission file을 통해 성능 평가
```

## Commands
```
# train
python main.py --num_classes=22 --lr=0.005 --cuda=True --num_epochs=10 --batch=16 --mode="train"

# test (for submission)
python main.py --batch=4 --model_name= "weights/1.pth" --prediction_file="prediction" --mode="test" 

#evaluate
python evaluate.py --prediction_file predictions/predictions_test.xml

```

## code issue
'''
ImportError : /lib64/libstdc++.so.6: version 'CXXABI_1.3.8' not found (required by ~)
 -> export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:your lib path (ex)/home/centos/anaconda3/envs/env_name/lib)
'''
## reference

[TORCHVISION OBJECT DETECTION FINETUNING TUTORIAL][1]

[1]: https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html
