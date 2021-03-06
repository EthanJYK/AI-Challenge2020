import os
import math
import datetime
import numpy as np
import time
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
import argparse
from torch import optim
from torch.autograd import Variable
import torchvision.utils


from dataloader import data_loader
from evaluation import evaluation_metrics
from model import SiameseNetwork
import torch.nn.functional as F

try:
    from nipa import nipa_data
    DATASET_PATH = nipa_data.get_data_root('deepfake')
except:
    DATASET_PATH = os.path.join('./data/')

def _infer(model, cuda, data_loader):
    res_id = []
    res_fc = []

    euclidean_distances = []
    for i, data in enumerate(data_loader):
        with torch.no_grad():
            iter1_, x0, iter2_, x1, label = data
            if cuda:
                x0 = x0.cuda()
                x1 = x1.cuda()
            output1, output2 = model(x0, x1)
            euclidean_distance = F.pairwise_distance(output1, output2).cpu()
            euclidean_distances.append(euclidean_distance)
    temp = sorted(euclidean_distances)[int(len(euclidean_distances) / 2)]
    for index, data in enumerate(data_loader):
        iter1_, x0, iter2_, x1, label = data
        image_name = iter1_[0] + ' ' + iter2_[0]
        if euclidean_distances[index] < temp:
            result = 0
        else:
            result = 1
        res_fc.append(result)
        res_id.append(image_name)
    return [res_id, res_fc]

def feed_infer(output_file, infer_func):
    prediction_name, prediction_class = infer_func()

    print('write output')
    predictions_str = []
    for index, name in enumerate(prediction_name):
        test_str = name + ' ' + str(prediction_class[index])
        predictions_str.append(test_str)
    with open(output_file, 'w') as file_writer:
        file_writer.write("\n".join(predictions_str))

    if os.stat(output_file).st_size == 0:
        raise AssertionError('output result of inference is nothing')

def validate(prediction_file, model, validate_dataloader, validate_label_file, cuda):
    feed_infer(prediction_file, lambda : _infer(model, cuda, data_loader=validate_dataloader))

    metric_result = evaluation_metrics(prediction_file, validate_label_file)
    print('Eval result: {:.4f}'.format(metric_result))
    return metric_result

def test(prediction_file, model, test_dataloader, cuda):
    feed_infer(prediction_file, lambda : _infer(model, cuda, data_loader=test_dataloader))


def save_model(model_name, model, optimizer):
    state = {
        'model': model.state_dict(),
        'optimizer': optimizer.state_dict(),
        # 'scheduler': scheduler.state_dict()
    }
    torch.save(state, os.path.join(DATASET_PATH, model_name + '.pth'))
    print('model saved')


def load_model(model_name, model, optimizer=None, scheduler=None):
    state = torch.load(os.path.join(DATASET_PATH, model_name))
    model.load_state_dict(state['model'])
    if optimizer is not None:
        optimizer.load_state_dict(state['optimizer'])
    if scheduler is not None:
        scheduler.load_state_dict(state['scheduler'])
    print('model loaded')



if __name__ == '__main__':
    # mode argument
    args = argparse.ArgumentParser()
    args.add_argument("--num_classes", type=int, default=2)
    args.add_argument("--lr", type=float, default=0.001)
    args.add_argument("--cuda", type=bool, default=True)
    args.add_argument("--num_epochs", type=int, default=100)
    args.add_argument("--print_iter", type=int, default=10)
    args.add_argument("--model_name", type=str, default="model.pth")
    args.add_argument("--prediction_file", type=str, default="prediction.txt")
    args.add_argument("--batch", type=int, default=64)
    args.add_argument("--mode", type=str, default="train")

    config = args.parse_args()

    num_classes = config.num_classes
    base_lr = config.lr
    cuda = config.cuda
    num_epochs = config.num_epochs
    print_iter = config.print_iter
    model_name = config.model_name
    prediction_file = config.prediction_file
    batch = config.batch
    mode = config.mode
    # create model

    model = SiameseNetwork()
    if mode == 'test':
        load_model(model_name, model)

    if cuda:
        model = model.cuda()

    if mode == 'train':
        # define loss function
        # loss_fn = nn.CrossEntropyLoss()
        # if cuda:
        #     loss_fn = loss_fn.cuda()
        class ContrastiveLoss(torch.nn.Module):
            """
            Contrastive loss function.
            Based on: http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
            """

            def __init__(self, margin=2.0):
                super(ContrastiveLoss, self).__init__()
                self.margin = margin

            def forward(self, output1, output2, label):
                euclidean_distance = F.pairwise_distance(output1, output2, keepdim=True)
                loss_contrastive = torch.mean((1 - label) * torch.pow(euclidean_distance, 2) +
                                              (label) * torch.pow(
                    torch.clamp(self.margin - euclidean_distance, min=0.0), 2))

                return loss_contrastive


        # set optimizer

        optimizer = optim.Adam(model.parameters(), lr=0.0005)
        scheduler = StepLR(optimizer, step_size=40, gamma=0.1)
        criterion = ContrastiveLoss()
        # Declare Optimizer

        # get data loader
        train_dataloader, _ = data_loader(root=DATASET_PATH, phase='train', batch_size=batch)
        validate_dataloader, validate_label_file = data_loader(root=DATASET_PATH, phase='validate', batch_size=1)
        time_ = datetime.datetime.now()
        num_batches = len(train_dataloader)
        #prediction_file = 'prediction.txt'
        counter = []
        loss_history = []
        iteration_number = 0

        # check parameter of model
        print("------------------------------------------------------------")
        total_params = sum(p.numel() for p in model.parameters())
        print("num of parameter : ", total_params)
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print("num of trainable_ parameter :", trainable_params)
        print("------------------------------------------------------------")

        # train
        for epoch in range(0, num_epochs):
            for iter_, data in enumerate(train_dataloader, 0):
                iter1_, img0, iter2_, img1, label = data
                img0, img1, label = img0.cuda(), img1.cuda(), label.cuda()
                optimizer.zero_grad()
                output1, output2 = model(img0, img1)
                loss_contrastive = criterion(output1, output2, label)
                loss_contrastive.backward()
                optimizer.step()
                if iter_ % print_iter == 0:
                    elapsed = datetime.datetime.now() - time_
                    expected = elapsed * (num_batches / print_iter)
                    _epoch = epoch + ((iter_ + 1) / num_batches)
                    print('[{:.3f}/{:d}] loss({}) '
                          'elapsed {} expected per epoch {}'.format(
                        _epoch, num_epochs, loss_contrastive.item(), elapsed, expected))
                    time_ = datetime.datetime.now()
            scheduler.step()
            validate(prediction_file, model, validate_dataloader, validate_label_file, cuda)
            time_ = datetime.datetime.now()
            elapsed = datetime.datetime.now() - time_
            print('[epoch {}] elapsed: {}'.format(epoch + 1, elapsed))
            if (epoch+1) % 10 == 0:
                save_model(str(epoch + 1), model, optimizer)


    elif mode == 'test':
        model.eval()
        # accuracy 확인
        test_dataloader, _ = data_loader(root=DATASET_PATH, phase='test', batch_size=1)
        #prediction_file = "prediction_test.txt"
        test(prediction_file, model, test_dataloader, cuda)
