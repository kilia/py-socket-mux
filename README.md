# py-socks-aggregation

## Intro

This project is to make a multi-path aggreator to maximize the bandwidth or minimize the lantency between nodes.

## Senario

One of the senario we see is like this:

* increase the tcp bandwidth in harsh network environments, where sometimes only one tcp stream is allowed
* e.g. using a proxy to watch youtube videos or send large files through ssh channel

## Main Conponents

* Window
* Conversation
* Tunnel

The connection graph is as follows:

client - window(seq) - conversation(id) - tunnel ~multi-path~ tunnel - conversation - window - server

