/**
 * 音频轨道预览控制器
 */

/**
 * WebView日志工具 - 将日志发送到Python日志系统
 */
const WebViewLog = {
    pyLogger: null,

    init(channel) {
        if (channel && channel.objects && channel.objects.pyLogger) {
            this.pyLogger = channel.objects.pyLogger;
        }
    },

    debug(message) {
        if (this.pyLogger) this.pyLogger.log('debug', String(message));
        console.debug('[WebView]', message);
    },

    info(message) {
        if (this.pyLogger) this.pyLogger.log('info', String(message));
        console.info('[WebView]', message);
    },

    warn(message) {
        if (this.pyLogger) this.pyLogger.log('warn', String(message));
        console.warn('[WebView]', message);
    },

    error(message) {
        if (this.pyLogger) this.pyLogger.log('error', String(message));
        console.error('[WebView]', message);
    }
};

class AudioPreview {
    constructor() {
        this.tracksContainer = document.getElementById('tracksContainer');
        this.timelineRuler = document.getElementById('timelineRuler');
        this.previewInfo = document.getElementById('previewInfo');
        this.maxDuration = 60;
        this.pixelsPerSecond = 10;
        this.tracks = [];

        this.init();
    }

    init() {
        this.showEmptyState();
        this.setupMessageHandler();
    }

    /**
     * 设置消息处理器（用于与PyQt通信）
     */
    setupMessageHandler() {
        // 检查是否在QWebEngineView中运行
        if (window.qt && window.qt.webChannelTransport) {
            // 使用QWebChannel与Python通信
            new QWebChannel(window.qt.webChannelTransport, (channel) => {
                window.pyBridge = channel.objects.pyBridge;
                // 初始化日志桥接器
                WebViewLog.init(channel);
                WebViewLog.info('WebView日志系统已初始化');
            });
        }

        // 监听来自父窗口的消息
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'updatePreview') {
                WebViewLog.debug('收到更新预览消息');
                this.updatePreview(event.data.tracks, event.data.maxDuration);
            }
        });
    }

    /**
     * 显示空状态
     */
    showEmptyState() {
        WebViewLog.debug('显示空状态');
        this.tracksContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎵</div>
                <div class="empty-state-text">请先选择音频文件以查看预览</div>
            </div>
        `;
        this.timelineRuler.innerHTML = '';
        this.previewInfo.innerHTML = '<span class="info-text">请先选择音频文件</span>';
    }

    /**
     * 更新预览
     * @param {Array} tracks - 轨道数据数组
     * @param {number} maxDuration - 最大时长（秒）
     */
    updatePreview(tracks, maxDuration) {
        WebViewLog.info(`更新预览: ${tracks ? tracks.length : 0} 个轨道片段, 总时长 ${maxDuration}s`);

        if (!tracks || tracks.length === 0) {
            this.showEmptyState();
            return;
        }

        this.tracks = tracks;
        this.maxDuration = maxDuration || 60;

        // 计算像素比例（确保最小宽度）
        const containerWidth = this.tracksContainer.clientWidth - 100; // 减去标签宽度
        this.pixelsPerSecond = Math.max(containerWidth / this.maxDuration, 5);

        this.renderRuler();
        this.renderTracks();
        this.updateInfo();
    }

    /**
     * 渲染时间轴标尺
     */
    renderRuler() {
        this.timelineRuler.innerHTML = '';

        const totalWidth = this.maxDuration * this.pixelsPerSecond;
        const majorInterval = this.calculateMajorInterval();
        const minorInterval = majorInterval / 5;

        // 主刻度
        for (let t = 0; t <= this.maxDuration; t += majorInterval) {
            const mark = document.createElement('div');
            mark.className = 'ruler-mark major';
            mark.style.left = `${t * this.pixelsPerSecond}px`;
            mark.setAttribute('data-time', this.formatTime(t));
            this.timelineRuler.appendChild(mark);
        }

        // 次刻度
        for (let t = 0; t <= this.maxDuration; t += minorInterval) {
            if (t % majorInterval !== 0) {
                const mark = document.createElement('div');
                mark.className = 'ruler-mark minor';
                mark.style.left = `${t * this.pixelsPerSecond}px`;
                this.timelineRuler.appendChild(mark);
            }
        }
    }

    /**
     * 计算主刻度间隔
     */
    calculateMajorInterval() {
        if (this.maxDuration <= 10) return 1;
        if (this.maxDuration <= 30) return 5;
        if (this.maxDuration <= 60) return 10;
        if (this.maxDuration <= 120) return 20;
        if (this.maxDuration <= 300) return 30;
        return 60;
    }

    /**
     * 格式化时间显示
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        if (mins > 0) {
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        return `${secs}s`;
    }

    /**
     * 渲染轨道
     */
    renderTracks() {
        this.tracksContainer.innerHTML = '';

        // 按轨道名称分组，相同名称的轨道显示在同一行
        const trackGroups = this.groupTracksByName(this.tracks);

        trackGroups.forEach((group, index) => {
            const trackRow = this.createTrackRow(group, index);
            this.tracksContainer.appendChild(trackRow);
        });
    }

    /**
     * 按轨道名称分组
     * 叠加轨道会单独分组显示，不会与原轨道重叠
     * 原肯定语轨道的所有循环片段会分到同一组
     */
    groupTracksByName(tracks) {
        const groups = new Map();

        tracks.forEach(track => {
            // 判断是否是叠加轨道
            const isOverlay = track.name.includes('叠加');

            // 获取基础名称（去除循环标记，但保留叠加标记）
            let baseName = track.name;

            if (isOverlay) {
                // 叠加轨道：按叠加层级分组（叠加1、叠加2等）
                const overlayMatch = track.name.match(/叠加\d+/);
                if (overlayMatch) {
                    baseName = `肯定语(${overlayMatch[0]})`;
                }
            } else {
                // 普通轨道：去除括号内的内容
                if (baseName.includes('(')) {
                    baseName = baseName.split('(')[0].trim();
                }
            }

            // 对于原肯定语轨道（非叠加），忽略overlayIndex，所有片段分到同一组
            // 对于叠加轨道，使用overlayIndex作为分组key的一部分
            let key;
            if (isOverlay) {
                const overlayIndex = track.overlayIndex || 0;
                key = `${baseName}_${overlayIndex}`;
            } else {
                key = baseName;
            }

            if (!groups.has(key)) {
                groups.set(key, {
                    baseName: baseName,
                    isOverlay: isOverlay,
                    overlayIndex: isOverlay ? (track.overlayIndex || 0) : 0,
                    tracks: []
                });
            }
            groups.get(key).tracks.push(track);
        });

        // 排序：主轨道在前，叠加轨道在后，叠加轨道按层级排序
        const sortedGroups = Array.from(groups.values()).sort((a, b) => {
            // 首先按是否叠加排序（非叠加在前）
            if (a.isOverlay !== b.isOverlay) {
                return a.isOverlay ? 1 : -1;
            }
            // 然后按overlayIndex排序
            return a.overlayIndex - b.overlayIndex;
        });

        return sortedGroups.map(g => g.tracks);
    }

    /**
     * 创建单个轨道行
     */
    createTrackRow(trackGroup, index) {
        const row = document.createElement('div');
        row.className = 'track-row';

        // 使用第一个轨道的名称作为标签
        const firstTrack = trackGroup[0];
        let labelName = firstTrack.name;

        // 对于叠加轨道，显示"肯定语(叠加X)"格式
        if (labelName.includes('叠加')) {
            const overlayMatch = labelName.match(/叠加\d+/);
            if (overlayMatch) {
                labelName = `肯定语(${overlayMatch[0]})`;
            } else {
                // 去除括号内的内容
                if (labelName.includes('(')) {
                    labelName = labelName.split('(')[0].trim();
                }
            }
        } else {
            // 去除括号内的内容
            if (labelName.includes('(')) {
                labelName = labelName.split('(')[0].trim();
            }
        }

        // 轨道标签
        const label = document.createElement('div');
        label.className = 'track-label';
        label.textContent = labelName;
        label.title = labelName;
        row.appendChild(label);

        // 轨道时间轴区域
        const timeline = document.createElement('div');
        timeline.className = 'track-timeline';

        // 为每个片段创建clip
        trackGroup.forEach(track => {
            const clip = this.createTrackClip(track);
            timeline.appendChild(clip);
        });

        row.appendChild(timeline);

        return row;
    }

    /**
     * 创建音频片段
     */
    createTrackClip(track) {
        // 计算片段位置
        let startTime = 0;

        if (track.overlayIndex > 0) {
            // 叠加轨道
            startTime = track.overlayIndex * track.overlayInterval;
        }

        // 如果有循环偏移，加上偏移量
        if (track.loopOffset !== undefined) {
            startTime += track.loopOffset;
        } else if (track.isLoop && track.overlayIndex > 0) {
            // 循环轨道的基础偏移
            startTime = track.overlayIndex * track.overlayInterval;
        } else if (track.isLoop && track.overlayIndex === 0) {
            // 主轨道的循环
            startTime = track.overlayIndex * (track.overlayInterval || 0);
        }

        const left = startTime * this.pixelsPerSecond;
        const width = Math.max(track.duration * this.pixelsPerSecond, 5);

        // 创建音频片段
        const clip = document.createElement('div');
        clip.className = `track-clip ${this.getTrackTypeClass(track)}`;
        clip.style.left = `${left}px`;
        clip.style.width = `${width}px`;

        // 片段内容
        const clipName = document.createElement('span');
        clipName.className = 'clip-name';
        // 显示简短名称
        let shortName = track.name;
        if (shortName.includes('(')) {
            const match = shortName.match(/\(([^)]+)\)/);
            if (match) {
                shortName = match[1]; // 只显示括号内的内容
            }
        }
        clipName.textContent = shortName;
        clip.appendChild(clipName);

        // 时长信息（只显示在足够宽的片段上）
        if (width > 40) {
            const clipInfo = document.createElement('span');
            clipInfo.className = 'clip-info';
            clipInfo.textContent = this.formatDuration(track.duration);
            clip.appendChild(clipInfo);

            // 音量信息（如果有且空间足够）
            if (track.volume !== undefined && track.volume !== 0 && width > 80) {
                const volumeInfo = document.createElement('span');
                volumeInfo.className = 'clip-info';
                volumeInfo.textContent = `${track.volume}dB`;
                clip.appendChild(volumeInfo);
            }
        }

        // 添加tooltip显示完整信息
        let tooltip = `${track.name}\n时长: ${this.formatDuration(track.duration)}`;
        if (track.volume !== undefined) {
            tooltip += `\n音量: ${track.volume}dB`;
        }
        if (track.isLoop) {
            tooltip += '\n模式: 循环播放';
        }
        if (track.isPartial) {
            tooltip += ' (片段)';
        }
        clip.title = tooltip;

        return clip;
    }

    /**
     * 获取轨道类型对应的CSS类
     */
    getTrackTypeClass(track) {
        if (track.name.includes('背景音乐')) return 'background';
        if (track.name.includes('叠加')) return 'affirmation-overlay';
        if (track.name.includes('肯定语')) return 'affirmation';
        if (track.name.includes('频率')) return 'frequency';
        return 'background';
    }

    /**
     * 格式化时长显示
     */
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds.toFixed(1)}s`;
        }
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(0);
        return `${mins}:${secs.padStart(2, '0')}`;
    }

    /**
     * 更新底部信息
     */
    updateInfo() {
        const trackCount = this.tracks.length;
        const durationText = `总时长: ${this.formatDuration(this.maxDuration)}`;
        this.previewInfo.innerHTML = `
            <span class="info-text">${trackCount} 个轨道片段</span>
            <span class="duration-text">${durationText}</span>
        `;
    }
}

// 初始化预览
const preview = new AudioPreview();

// 暴露给全局，方便外部调用
window.updateAudioPreview = (tracks, maxDuration) => {
    WebViewLog.info('外部调用 updateAudioPreview');
    preview.updatePreview(tracks, maxDuration);
};

window.clearAudioPreview = () => {
    WebViewLog.info('外部调用 clearAudioPreview');
    preview.showEmptyState();
};

WebViewLog.info('AudioPreview 模块已加载完成');
