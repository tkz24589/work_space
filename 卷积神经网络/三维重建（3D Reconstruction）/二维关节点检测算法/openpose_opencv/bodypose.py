#!/usr/bin/python3
#!--*-- coding: utf-8 --*--
from __future__ import division

import json

import cv2
import time
import numpy as np
import matplotlib.pyplot as plt
import os


class general_pose_model(object):
    def __init__(self, modelpath, mode="COCO"):
        # 指定采用的模型
        #   Body25: 25 points
        #   COCO:   18 points
        #   MPI:    15 points
        self.inWidth = 368
        self.inHeight = 368
        self.threshold = 0
        if mode == "BODY25":
            self.pose_net = self.general_body25_model(modelpath)
        elif mode == "COCO":
            self.pose_net = self.general_coco_model(modelpath)
        elif mode == "MPI":
            self.pose_net = self.get_mpi_model(modelpath)


    def get_mpi_model(self, modelpath):
        self.points_name = {
            "Head": 0, "Neck": 1,
            "RShoulder": 2, "RElbow": 3, "RWrist": 4,
            "LShoulder": 5, "LElbow": 6, "LWrist":
            7, "RHip": 8, "RKnee": 9, "RAnkle": 10,
            "LHip": 11, "LKnee": 12, "LAnkle": 13,
            "Chest": 14, "Background": 15 }
        self.num_points = 15
        self.point_pairs = [[0, 1], [1, 2], [2, 3],
                            [3, 4], [1, 5], [5, 6],
                            [6, 7], [1, 14],[14, 8],
                            [8, 9], [9, 10], [14, 11],
                            [11, 12], [12, 13]
                            ]
        prototxt = os.path.join(
            modelpath,
            "pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt")
        caffemodel = os.path.join(
            modelpath,
            "pose/mpi/pose_iter_160000.caffemodel")
        mpi_model = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)

        return mpi_model


    def general_coco_model(self, modelpath):
        self.points_name = {
            "Nose": 0, "Neck": 1,
            "RShoulder": 2, "RElbow": 3, "RWrist": 4,
            "LShoulder": 5, "LElbow": 6, "LWrist": 7,
            "RHip": 8, "RKnee": 9, "RAnkle": 10,
            "LHip": 11, "LKnee": 12, "LAnkle": 13,
            "REye": 14, "LEye": 15,
            "REar": 16, "LEar": 17,
            "Background": 18}
        self.num_points = 18
        self.point_pairs = [[1, 0], [1, 2], [1, 5],
                            [2, 3], [3, 4], [5, 6],
                            [6, 7], [1, 8], [8, 9],
                            [9, 10], [1, 11], [11, 12],
                            [12, 13], [0, 14], [0, 15],
                            [14, 16], [15, 17]]
        prototxt   = os.path.join(
            modelpath,
            "pose/coco/pose_deploy_linevec.prototxt")
        caffemodel = os.path.join(
            modelpath,
            "pose/coco/pose_iter_440000.caffemodel")
        coco_model = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)

        return coco_model


    def general_body25_model(self, modelpath):
        self.num_points = 25
        self.point_pairs = [[1, 0], [1, 2], [1, 5],
                            [2, 3], [3, 4], [5, 6],
                            [6, 7], [0, 15], [15, 17],
                            [0, 16], [16, 18], [1, 8],
                            [8, 9], [9, 10], [10, 11],
                            [11, 22], [22, 23], [11, 24],
                            [8, 12], [12, 13], [13, 14],
                            [14, 19], [19, 20], [14, 21]]
        prototxt   = os.path.join(
            modelpath,
            "pose/body_25/pose_deploy.prototxt")
        caffemodel = os.path.join(
            modelpath,
            "pose/body_25/pose_iter_584000.caffemodel")
        coco_model = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)

        return coco_model


    def predict(self, imgfile):
        img_cv2 = cv2.imread(imgfile)
        img_height, img_width, _ = img_cv2.shape
        inpBlob = cv2.dnn.blobFromImage(img_cv2,
                                        1.0 / 255,
                                        (self.inWidth, self.inHeight),
                                        (0, 0, 0),
                                        swapRB=False,
                                        crop=False)
        self.pose_net.setInput(inpBlob)
        self.pose_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.pose_net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)

        output = self.pose_net.forward()

        H = output.shape[2]
        W = output.shape[3]
        print(output.shape)

        # vis heatmaps
        # self.vis_heatmaps(img_file, output)

        #
        points = []
        for idx in range(self.num_points):
            probMap = output[0, idx, :, :] # confidence map.

            # Find global maxima of the probMap.
            minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

            # Scale the point to fit on the original image
            x = (img_width * point[0]) / W
            y = (img_height * point[1]) / H

            if prob > self.threshold:
                points.append((int(x), int(y)))
            else:
                points.append(None)

        return points


    def vis_heatmaps(self, imgfile, net_outputs):
        img_cv2 = cv2.imread(imgfile)
        plt.figure(figsize=[10, 10])

        for pdx in range(self.num_points):
            probMap = net_outputs[0, pdx, :, :]
            probMap = cv2.resize(
                probMap,
                (img_cv2.shape[1], img_cv2.shape[0])
            )
            plt.subplot(5, 5, pdx+1)
            plt.imshow(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
            plt.imshow(probMap, alpha=0.6)
            plt.colorbar()
            plt.axis("off")
            plt.imsave('ressult_points'+str(pdx)+'.jpg', probMap)
        plt.show()

    def save_keypoints(self, json_path, img_name, poses):
        # joints
        filename = json_path + '' + img_name + '_keypoints.json'
        json_file = {"version": 1.2,
                     "people": [{"pose_keypoints_2d": []
                                 }]}
        for i in poses:
            json_file['people'][0]['pose_keypoints_2d'].append(np.float(i[0]))
            json_file['people'][0]['pose_keypoints_2d'].append(np.float(i[1]))
            json_file['people'][0]['pose_keypoints_2d'].append(np.float(2))
        with open(filename, 'w') as file_obj:
            json.dump(json_file, file_obj)
        return filename

    def read_openpose(self, json_file, gt_part, dataset):
        # get only the arms/legs joints
        op_to_12 = [11, 10, 9, 12, 13, 14, 4, 3, 2, 5, 6, 7]
        # read the openpose detection
        json_data = json.load(open(json_file, 'r'))
        people = json_data['people']
        if len(people) == 0:
            # no openpose detection
            keyp25 = np.zeros([25, 3])
        else:
            # size of person in pixels
            scale = max(max(gt_part[:, 0]) - min(gt_part[:, 0]), max(gt_part[:, 1]) - min(gt_part[:, 1]))
            # go through all people and find a match
            dist_conf = np.inf * np.ones(len(people))
            for i, person in enumerate(people):
                # openpose keypoints
                op_keyp25 = np.reshape(person['pose_keypoints_2d'], [25, 3])
                op_keyp12 = op_keyp25[op_to_12, :2]
                op_conf12 = op_keyp25[op_to_12, 2:3] > 0
                # all the relevant joints should be detected
                if min(op_conf12) > 0:
                    # weighted distance of keypoints
                    dist_conf[i] = np.mean(np.sqrt(np.sum(op_conf12 * (op_keyp12 - gt_part[:12, :2]) ** 2, axis=1)))
            # closest match
            p_sel = np.argmin(dist_conf)
            # the exact threshold is not super important but these are the values we used
            if dataset == 'mpii':
                thresh = 30
            elif dataset == 'coco':
                thresh = 10
            else:
                thresh = 0
            # dataset-specific thresholding based on pixel size of person
            if min(dist_conf) / scale > 0.1 and min(dist_conf) < thresh:
                keyp25 = np.zeros([25, 3])
            else:
                keyp25 = np.reshape(people[p_sel]['pose_keypoints_2d'], [25, 3])
        return keyp25


    def vis_pose(self, imgfile, points):
        img_cv2 = cv2.imread(imgfile)
        img_cv2_copy = np.copy(img_cv2)
        for idx in range(len(points)):
            if points[idx]:
                cv2.circle(img_cv2_copy,
                           points[idx],
                           8,
                           (0, 255, 255),
                           thickness=-1,
                           lineType=cv2.FILLED)
                cv2.putText(img_cv2_copy,
                            "{}".format(idx),
                            points[idx],
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2,
                            lineType=cv2.LINE_AA)

        # Draw Skeleton
        cv2.imwrite("result1.jpg", img_cv2_copy)
        for pair in self.point_pairs:
            partA = pair[0]
            partB = pair[1]

            if points[partA] and points[partB]:
                cv2.line(img_cv2,
                         points[partA],
                         points[partB],
                         (0, 255, 255), 5)
                cv2.circle(img_cv2,
                           points[partA],
                           8,
                           (0, 0, 255),
                           thickness=-1,
                           lineType=cv2.FILLED)

        cv2.imwrite("result2.jpg", img_cv2)

        plt.figure(figsize=[10, 10])
        plt.subplot(1, 2, 1)
        plt.imshow(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.subplot(1, 2, 2)
        plt.imshow(cv2.cvtColor(img_cv2_copy, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.show()


if __name__ == '__main__':
    print("[INFO]Pose estimation.")
    img_path = ""
    img_list = os.listdir(img_path)
    for img in img_list:
        img_file = img_path + img
        #

        modelpath = "models"
        pose_model = general_pose_model(modelpath, mode="BODY25")

        res_points = pose_model.predict(img_file)
        # pose_model.vis_pose(img_file, res_points)
        file_name = pose_model.save_keypoints(img_path + 'json/',str(img).split('.')[0], res_points)