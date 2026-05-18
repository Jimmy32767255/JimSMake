/**
 * 音频轨道预览控制器
 */
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
            });
        }
        
        // 监听来自父窗口的消息
        window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'updatePreview') {
                this.updatePreview(event.data.tracks, event.data.maxDuration);
            }
        });
    }
    
    /**
     * 显示空状态
     */
    showEmptyState() {
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
        
        this.tracks.forEach((track, index) => {
            const trackRow = this.createTrackRow(track, index);
            this.tracksContainer.appendChild(trackRow);
        });
    }
    
    /**
     * 创建单个轨道行
     */
    createTrackRow(track, index) {
        const row = document.createElement('div');
        row.className = 'track-row';
        
        // 轨道标签
        const label = document.createElement('div');
        label.className = 'track-label';
        label.textContent = track.name;
        label.title = track.name;
        row.appendChild(label);
        
        // 轨道时间轴区域
        const timeline = document.createElement('div');
        timeline.className = 'track-timeline';
        
        // 计算片段位置和宽度
        const startTime = track.overlayIndex ? track.overlayIndex * track.overlayInterval : 0;
        const left = startTime * this.pixelsPerSecond;
        const width = Math.max(track.duration * this.pixelsPerSecond, 20);
        
        // 创建音频片段
        const clip = document.createElement('div');
        clip.className = `track-clip ${this.getTrackTypeClass(track)}`;
        clip.style.left = `${left}px`;
        clip.style.width = `${width}px`;
        
        // 片段内容
        const clipName = document.createElement('span');
        clipName.className = 'clip-name';
        clipName.textContent = track.name;
        clip.appendChild(clipName);
        
        // 时长信息
        const clipInfo = document.createElement('span');
        clipInfo.className = 'clip-info';
        clipInfo.textContent = this.formatDuration(track.duration);
        clip.appendChild(clipInfo);
        
        // 音量信息（如果有）
        if (track.volume !== undefined && track.volume !== 0) {
            const volumeInfo = document.createElement('span');
            volumeInfo.className = 'clip-info';
            volumeInfo.textContent = `${track.volume}dB`;
            clip.appendChild(volumeInfo);
        }
        
        timeline.appendChild(clip);
        row.appendChild(timeline);
        
        return row;
    }
    
    /**
     * 获取轨道类型对应的CSS类
     */
    getTrackTypeClass(track) {
        if (track.name.includes('背景音乐')) return 'background';
        if (track.name.includes('肯定语') && track.overlayIndex > 0) return 'affirmation-overlay';
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
            <span class="info-text">${trackCount} 个轨道</span>
            <span class="duration-text">${durationText}</span>
        `;
    }
}

// 初始化预览
const preview = new AudioPreview();

// 暴露给全局，方便外部调用
window.updateAudioPreview = (tracks, maxDuration) => {
    preview.updatePreview(tracks, maxDuration);
};

window.clearAudioPreview = () => {
    preview.showEmptyState();
};
