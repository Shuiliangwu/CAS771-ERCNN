import torchvision.transforms as transforms
from utils.config_loader import ConfigLoader
import torchvision.datasets as datasets
from torch.utils.data import DataLoader
import torch

from datasets.dataset_loader import MyDataSet, ImageNet
from models.models import Net
from utils.trainer import Trainer
from visualize.visualizer import AccuracyPlotter, Imshow


# Load the config file
config = ConfigLoader.get_config()
ConfigLoader.print_config(config)

# Load the dataset
datasetConf = ConfigLoader.get_config(config_path="datasets/dataset_conf.yaml")
ConfigLoader.print_config(datasetConf)
dataset_index = config['dataset_index'] - 1

if config['pretrain']:

    testset_loader = ImageNet(datasetConf['ImageNet_root'], 'val').make_subset(0, config['pretrain_classes']).loader(
        batch_size=config['batch_size'])
    trainset_loader = ImageNet(datasetConf['ImageNet_root'], 'train').make_subset(0, config['pretrain_classes']).loader(
        batch_size=config['batch_size'])
    images, labels = next(iter(trainset_loader))
    print('Pretrain on ImageNet')
    # images, labels = next(iter(trainset_loader))
    # for i in range(0, 32):
    #     Imshow.imshow(images[i], images[i*2])
else:
    trainset_loader = DataLoader(MyDataSet(datasetConf['train_root'][dataset_index], datasetConf['train_label']
                                           [dataset_index]), batch_size=config['batch_size'], shuffle=True, num_workers=0)
    testset_loader = DataLoader(MyDataSet(datasetConf['test_root'][dataset_index], datasetConf['test_label']
                                          [dataset_index]), batch_size=config['batch_size'], shuffle=True, num_workers=0)

# Visualize the images after the adaptation network
if config['view_adaptated_image']:
    net = Net(key_size=datasetConf['key_size'][dataset_index], num_classes=datasetConf['num_classes']
              [dataset_index], model_name=config['model_name'], adaptation=config['adaptation'], adaptation_pretrained=config['adaptation_pretrained'])

    images, labels = next(iter(testset_loader))
    for i in range(0, 32):
        Imshow.imshow(images[i], net.forward_adaptation(
            images[i]), f'./log/{ConfigLoader.generate_model_name(config)}/adapted_images/image{i}.png')

if config['test']:
    # Load the model
    net = Net(key_size=datasetConf['key_size'][dataset_index], num_classes=datasetConf['num_classes']
              [dataset_index], model_name=config['model_name'], adaptation=config['adaptation'], resume=config['resume'], adaptation_pretrained=config['adaptation_pretrained'], cnn_pretrained=config['cnn_pretrained'], self_pretrained=config['self_pretrained'], Test=config['test'])
    # Load the device
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print('Testing on ' + device.type)

    # Load the trainer
    trainer = Trainer(net=net, trainset_loader=trainset_loader,
                      testset_loader=testset_loader, device=device, config=config)

    # Test the model
    trainer.test()
else:
    for round in range(1, config['training_round'] + 1):

        # Load the model
        if config['pretrain']:
            net = Net(key_size=datasetConf['key_size'][dataset_index], num_classes=config['pretrain_classes'],
                      model_name=config['model_name'], resume=config['resume'], adaptation=False, adaptation_pretrained=False, cnn_pretrained=False)
        else:
            net = Net(key_size=datasetConf['key_size'][dataset_index], num_classes=datasetConf['num_classes']
                      [dataset_index], model_name=config['model_name'], adaptation=config['adaptation'], resume=config['resume'], adaptation_pretrained=config['adaptation_pretrained'], cnn_pretrained=config['cnn_pretrained'], self_pretrained=config['self_pretrained'])
        # Load the device
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print('Training on ' + device.type)

        # Load the trainer
        trainer = Trainer(net=net, trainset_loader=trainset_loader,
                          testset_loader=testset_loader, device=device, config=config)

        # Train the model
        trainer.train(round=round, resume=config['resume'])

        # Visualize the accuracy
        AccuracyPlotter(config, ConfigLoader.generate_model_name(
            config)).plot(show=False, round=round)
